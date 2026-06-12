"""
CSV export and import functions for lead data.
"""
import csv
import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)


def export_csv(leads: List[Dict], output_path: str):
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
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, restval="", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(leads)

    logger.info("Exported %d leads to %s", len(leads), output_path)


def load_leads_from_csv(path: str) -> List[Dict]:
    """Load leads from a previously exported CSV."""
    with open(path, "r", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        return list(reader)
