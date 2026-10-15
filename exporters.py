"""
CSV export/import functions and shared ordering for lead data.
"""

import csv
import logging
import math
import os

logger = logging.getLogger(__name__)

SORT_KEYS = ("score", "rating", "reviews")

_SORT_FIELDS = {
    "score": "lead_score",
    "rating": "google_rating",
    "reviews": "review_count",
}


def to_number(value) -> float | None:
    """Coerce a lead value (number or CSV string) to float; None when missing, invalid or non-finite."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
    return number if math.isfinite(number) else None


def sort_value(value) -> str:
    """Render a lead value as a plain numeric string for `data-sort` attributes ('' when missing)."""
    number = to_number(value)
    if number is None:
        return ""
    return str(int(number)) if number.is_integer() else repr(number)


def sort_leads(leads: list[dict], by: str = "score") -> list[dict]:
    """Return a new list sorted descending by `by`.

    Leads with a missing, empty or unparseable value always sort last.
    Ties (including among missing values) are broken by lead_score descending;
    the sort is stable for full ties.
    """
    if by not in _SORT_FIELDS:
        raise ValueError(f"Unknown sort key: {by!r} (expected one of {SORT_KEYS})")
    field = _SORT_FIELDS[by]

    def key(lead: dict) -> tuple:
        value = to_number(lead.get(field))
        score = to_number(lead.get("lead_score")) or 0.0
        missing = value is None
        return (missing, -(value or 0.0), -score)

    return sorted(leads, key=key)


def export_csv(leads: list[dict], output_path: str):
    """Write leads to CSV file."""
    fieldnames = [
        "business_name",
        "industry",
        "contact_person",
        "phone",
        "email",
        "address",
        "city",
        "website",
        "whatsapp_link",
        "facebook_url",
        "instagram_handle",
        "linkedin_url",
        "booking_links",
        "google_rating",
        "review_count",
        "lead_score",
        "lead_tier",
        "scoring_notes",
        "source",
        "date_found",
    ]

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval="", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    logger.info("Exported %d leads to %s", len(leads), output_path)


def load_leads_from_csv(path: str) -> list[dict]:
    """Load leads from a previously exported CSV."""
    with open(path, encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        return list(reader)
