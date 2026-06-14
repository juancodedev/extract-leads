"""
Tests for fuzzy deduplication of leads by business name.
"""
import pytest
from pipeline import deduplicate_leads


def make_lead(name: str, score: int = 50, **extra) -> dict:
    """Helper to build a minimal lead for dedup testing."""
    lead = {
        "business_name": name,
        "lead_score": score,
    }
    lead.update(extra)
    return lead


class TestDeduplication:
    """Fuzzy dedup using token_sort_ratio at threshold 85."""

    def test_identical_names_merge(self):
        leads = [
            make_lead("Barbería El Corte", score=80),
            make_lead("Barbería El Corte", score=60),
        ]
        result = deduplicate_leads(leads)
        assert len(result) == 1
        # Highest scored lead kept
        assert result[0]["lead_score"] == 80

    def test_different_names_kept(self):
        leads = [
            make_lead("Barbería El Corte", score=80),
            make_lead("Cafetería La Esquina", score=70),
        ]
        result = deduplicate_leads(leads)
        assert len(result) == 2

    def test_fuzzy_match_merged(self):
        """Names that differ slightly are merged."""
        leads = [
            make_lead("Barberia El Corte", score=85),       # without accent
            make_lead("Barbería El Corte", score=60),        # with accent
        ]
        result = deduplicate_leads(leads)
        # "barberia el corte" vs "barbería el corte" → token_sort_ratio should be very high
        assert len(result) == 1
        assert result[0]["lead_score"] == 85

    def test_fuzzy_match_with_extra_words(self):
        """Extra words like 'Spa' added to the name."""
        leads = [
            make_lead("Peluquería Spa Belleza", score=90),
            make_lead("Peluquería Belleza", score=75),
        ]
        result = deduplicate_leads(leads)
        # "peluquería spa belleza" vs "peluquería belleza" → token overlap
        # token_sort_ratio: {'peluquería', 'spa', 'belleza'} vs {'peluquería', 'belleza'}
        # intersection=2, union=3 → 2/3 = 66.7? That's below 85.
        # Actually token_sort_ratio sorts tokens, then compares as strings. Let me think...
        # Sorted: "belleza peluquería spa" vs "belleza peluquería" → these are very close but
        # the extra "spa" will cause partial ratio. Actually let me verify: token_sort_ratio
        # sorts tokens alphabetically then does partial_ratio. 
        # String1: "belleza peluqueria spa", String2: "belleza peluqueria"
        # partial_ratio("belleza peluqueria spa", "belleza peluqueria") 
        # The shorter (String2) is a substring of the longer → 100% match.
        assert len(result) == 1
        assert result[0]["lead_score"] == 90

    def test_completely_different_names_kept(self):
        leads = [
            make_lead("Barbería El Corte", score=80),
            make_lead("Clínica Dental Sonrisa", score=70),
        ]
        result = deduplicate_leads(leads)
        assert len(result) == 2

    def test_empty_list(self):
        result = deduplicate_leads([])
        assert result == []

    def test_single_lead(self):
        leads = [make_lead("Único", score=100)]
        result = deduplicate_leads(leads)
        assert len(result) == 1
        assert result[0]["business_name"] == "Único"

    def test_case_insensitive(self):
        leads = [
            make_lead("BARBERÍA EL CORTE", score=90),
            make_lead("barbería el corte", score=70),
        ]
        result = deduplicate_leads(leads)
        assert len(result) == 1
        assert result[0]["lead_score"] == 90

    def test_custom_threshold(self):
        """With a very low threshold, even very different names merge."""
        leads = [
            make_lead("Barbería X", score=80),
            make_lead("Cafetería Y", score=70),
        ]
        # Threshold 0 → everything merges
        result = deduplicate_leads(leads, threshold=0)
        assert len(result) == 1

    def test_threshold_100_exact_match_only(self):
        """At threshold 100, only exact matches merge."""
        leads = [
            make_lead("Barbería El Corte", score=90),
            make_lead("Barbería El Corte", score=70),
            make_lead("Barberia El Corte", score=80),  # no accent
        ]
        result = deduplicate_leads(leads, threshold=100)
        # First two merge, third kept because accent difference breaks 100% match
        # Actually "Barbería El Corte" vs "Barberia El Corte" — token_sort sorts 
        # "corte el barbería" vs "corte el barberia" — these differ by one char (í vs i)
        # partial_ratio would be very high but not 100
        assert len(result) == 2
        # The exact match pair merged to score 90
        scores = {r["lead_score"] for r in result}
        assert scores == {90, 80}
