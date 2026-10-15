"""Tests for the shared lead sorting helper and its use in the HTML report."""

import pytest

from exporters import SORT_KEYS, sort_leads


def _names(leads: list[dict]) -> list[str]:
    return [lead["business_name"] for lead in leads]


class TestSortLeads:
    def test_sort_keys_exposed(self):
        assert SORT_KEYS == ("score", "rating", "reviews")

    def test_default_sorts_by_score_desc(self):
        leads = [
            {"business_name": "a", "lead_score": 40},
            {"business_name": "b", "lead_score": 90},
            {"business_name": "c", "lead_score": 60},
        ]
        assert _names(sort_leads(leads)) == ["b", "c", "a"]

    def test_sort_by_rating_coerces_strings(self):
        leads = [
            {"business_name": "a", "google_rating": "4.2", "lead_score": "50"},
            {"business_name": "b", "google_rating": "4.9", "lead_score": "50"},
            {"business_name": "c", "google_rating": 4.5, "lead_score": 50},
        ]
        assert _names(sort_leads(leads, by="rating")) == ["b", "c", "a"]

    def test_sort_by_reviews_numeric_not_lexical(self):
        leads = [
            {"business_name": "a", "review_count": "99"},
            {"business_name": "b", "review_count": "1200"},
            {"business_name": "c", "review_count": "312"},
        ]
        assert _names(sort_leads(leads, by="reviews")) == ["b", "c", "a"]

    def test_missing_empty_and_invalid_values_sort_last(self):
        leads = [
            {"business_name": "empty", "review_count": "", "lead_score": 99},
            {"business_name": "none", "review_count": None, "lead_score": 98},
            {"business_name": "bad", "review_count": "n/a", "lead_score": 97},
            {"business_name": "missing", "lead_score": 96},
            {"business_name": "zero", "review_count": "0", "lead_score": 1},
            {"business_name": "ten", "review_count": 10, "lead_score": 1},
        ]
        result = _names(sort_leads(leads, by="reviews"))
        assert result[:2] == ["ten", "zero"]
        assert set(result[2:]) == {"empty", "none", "bad", "missing"}

    def test_nan_sorts_last(self):
        leads = [
            {"business_name": "nan", "google_rating": "nan", "lead_score": 99},
            {"business_name": "ok", "google_rating": "3.1", "lead_score": 1},
        ]
        assert _names(sort_leads(leads, by="rating")) == ["ok", "nan"]

    def test_missing_values_ordered_by_score_among_themselves(self):
        leads = [
            {"business_name": "low", "google_rating": "", "lead_score": 10},
            {"business_name": "high", "google_rating": "", "lead_score": 80},
            {"business_name": "rated", "google_rating": "3.0", "lead_score": 5},
        ]
        assert _names(sort_leads(leads, by="rating")) == ["rated", "high", "low"]

    def test_tiebreak_by_score_desc(self):
        leads = [
            {"business_name": "a", "google_rating": "4.5", "lead_score": 30},
            {"business_name": "b", "google_rating": "4.5", "lead_score": "70"},
            {"business_name": "c", "google_rating": "4.5", "lead_score": 50},
        ]
        assert _names(sort_leads(leads, by="rating")) == ["b", "c", "a"]

    def test_stable_for_full_ties(self):
        leads = [{"business_name": n, "lead_score": 50} for n in "abcd"]
        assert _names(sort_leads(leads)) == ["a", "b", "c", "d"]

    def test_does_not_mutate_input(self):
        leads = [{"business_name": "a", "lead_score": 1}, {"business_name": "b", "lead_score": 2}]
        sort_leads(leads)
        assert _names(leads) == ["a", "b"]

    def test_unknown_key_raises(self):
        with pytest.raises(ValueError):
            sort_leads([], by="name")


class TestExportHtmlSortBy:
    def test_report_respects_sort_by(self, tmp_path):
        from reporters import export_html

        leads = [
            {"business_name": "AlphaShop", "review_count": "5", "lead_score": 90, "lead_tier": "HOT"},
            {"business_name": "BetaShop", "review_count": "500", "lead_score": 10, "lead_tier": "COLD"},
        ]
        out = tmp_path / "r.html"
        export_html(leads, str(out), sort_by="reviews")
        html = out.read_text(encoding="utf-8")
        assert html.index("BetaShop") < html.index("AlphaShop")

    def test_report_default_is_score(self, tmp_path):
        from reporters import export_html

        leads = [
            {"business_name": "AlphaShop", "review_count": "5", "lead_score": 90, "lead_tier": "HOT"},
            {"business_name": "BetaShop", "review_count": "500", "lead_score": 10, "lead_tier": "COLD"},
        ]
        out = tmp_path / "r.html"
        export_html(leads, str(out))
        html = out.read_text(encoding="utf-8")
        assert html.index("AlphaShop") < html.index("BetaShop")


class TestCliSortByArg:
    def test_help_lists_sort_by(self):
        import subprocess
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "cli.py", "--help"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root,
        )
        assert "--sort-by" in result.stdout
