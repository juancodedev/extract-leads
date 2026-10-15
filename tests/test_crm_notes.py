"""Tests for the CRM `notas` field (Google rating and review count)."""

import json
import re

from cli import _build_crm_notes

BASE = "Lead Score: 70 | Industria: Barbería | Ciudad: Ñuñoa"


def _lead(**extra) -> dict:
    lead = {"lead_score": 70, "industry": "Barbería", "city": "Ñuñoa"}
    lead.update(extra)
    return lead


class TestBuildCrmNotes:
    def test_rating_and_reviews_appended(self):
        notes = _build_crm_notes(_lead(google_rating=4.7, review_count=312))
        assert notes == f"{BASE} | Rating: 4.7 (312 reseñas)"

    def test_csv_string_values(self):
        notes = _build_crm_notes(_lead(google_rating="4.7", review_count="312"))
        assert notes == f"{BASE} | Rating: 4.7 (312 reseñas)"

    def test_single_review_is_singular(self):
        notes = _build_crm_notes(_lead(google_rating="5.0", review_count="1"))
        assert notes == f"{BASE} | Rating: 5.0 (1 reseña)"

    def test_rating_without_reviews(self):
        for reviews in ("", None, "0", "n/a"):
            notes = _build_crm_notes(_lead(google_rating="4.2", review_count=reviews))
            assert notes == f"{BASE} | Rating: 4.2", reviews

    def test_no_rating_keeps_notes_unchanged(self):
        for rating in ("", None, "n/a"):
            notes = _build_crm_notes(_lead(google_rating=rating, review_count="312"))
            assert notes == BASE, rating

    def test_missing_base_fields_use_na(self):
        assert _build_crm_notes({}) == "Lead Score: N/A | Industria: N/A | Ciudad: N/A"


class TestReportCrmPayload:
    def test_leads_json_carries_rating_and_reviews(self, tmp_path, monkeypatch):
        from reporters import export_html

        for var in ("CRM_API_URL", "CRM_API_EMAIL", "CRM_API_PASSWORD"):
            monkeypatch.setenv(var, "x")
        out = tmp_path / "r.html"
        export_html(
            [{"business_name": "A", "google_rating": "4.7", "review_count": "312", "lead_score": 70}],
            str(out),
        )
        html = out.read_text(encoding="utf-8")
        match = re.search(
            r'<script id="leads-data" type="application/json">(.*?)</script>', html, re.S
        )
        assert match
        data = json.loads(match.group(1))
        assert data[0]["google_rating"] == "4.7"
        assert data[0]["review_count"] == "312"
        assert "function crmRatingNote" in html
