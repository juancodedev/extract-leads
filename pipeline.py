#!/usr/bin/env python3
"""
Lead Extraction Pipeline - CLI tool.

Finds, enriches, scores, and exports business leads automatically
using Google Places API and optional Hunter.io enrichment.

Usage:
    # Set your API key and run
    export GOOGLE_PLACES_API_KEY="your_key_here"
    python pipeline.py

    # With Hunter.io for email enrichment
    export HUNTER_API_KEY="your_key_here"
    python pipeline.py

    # Custom config and output
    python pipeline.py --config my_config.yaml --output my_leads.csv --limit 50
"""
import argparse
import csv
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

import yaml

from extractor import PlacesExtractor
from enricher import Enricher
from lead_scorer import LeadScorer

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(path: str) -> Dict:
    """Load YAML configuration file."""
    if not os.path.exists(path):
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(
    config: Dict,
    api_key: str,
    hunter_key: str = "",
    limit: int = 0,
) -> List[Dict]:
    """Execute the full extraction pipeline.

    For each industry keyword x location pair, searches Google Places,
    enriches results, and applies scoring.

    Returns:
        List of scored lead dicts.
    """
    extractor = PlacesExtractor(api_key)
    enricher = Enricher(hunter_key if hunter_key else None)
    scorer = LeadScorer(config)

    all_leads: List[Dict] = []
    seen_names: set = set()

    search_config = config.get("search", {})
    industries = search_config.get("industries", [])
    locations = search_config.get("locations", [])

    total_combos = len(industries) * len(locations)
    done = 0

    for industry in industries:
        for keyword in industry.get("keywords", []):
            for loc in locations:
                if limit and len(all_leads) >= limit:
                    break
                done += 1

                logger.info(
                    "[%d/%d] Searching '%s' in %s, %s",
                    done, total_combos, keyword, loc["city"], loc["region"],
                )

                try:
                    results = extractor.search_businesses(
                        keyword, f"{loc['city']}, {loc['region']}"
                    )
                except Exception as e:
                    logger.error("Search failed: %s", e)
                    continue

                for place in results:
                    name = place.get("business_name", "")
                    if not name or name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    industry_name = LeadScorer.classify_industry(
                        place.get("types", []),
                        name,
                        config,
                    )

                    lead = {
                        "business_name": name,
                        "industry": industry_name,
                        "contact_person": "",
                        "phone": (
                            place.get("international_phone")
                            or place.get("phone", "")
                        ),
                        "email": "",
                        "address": place.get("address", ""),
                        "city": LeadScorer.extract_city(
                            place.get("address", ""), config
                        ),
                        "website": place.get("website", ""),
                        "facebook_url": "",
                        "instagram_handle": "",
                        "linkedin_url": "",
                        "google_rating": place.get("rating"),
                        "review_count": place.get("total_ratings", 0),
                        "google_type": ", ".join(place.get("types", [])),
                        "source": "Google Maps",
                        "date_found": datetime.now().strftime("%Y-%m-%d"),
                    }

                    # Email enrichment via Hunter.io
                    if lead["website"] and hunter_key:
                        domain = Enricher.extract_domain(lead["website"])
                        if domain:
                            email = enricher.find_email(domain)
                            if email:
                                lead["email"] = email

                    # Social media detection from website
                    if lead["website"]:
                        social = enricher.detect_social(
                            lead["website"], name
                        )
                        lead["facebook_url"] = social.get("facebook") or ""
                        lead["instagram_handle"] = social.get("instagram") or ""
                        lead["linkedin_url"] = social.get("linkedin") or ""

                    # Scoring
                    lead = scorer.score(lead)
                    all_leads.append(lead)

                    if limit and len(all_leads) >= limit:
                        break

            if limit and len(all_leads) >= limit:
                break

    return all_leads


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
        "facebook_url",
        "instagram_handle",
        "linkedin_url",
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


def print_summary(leads: List[Dict]):
    """Print a summary of results to stdout."""
    if not leads:
        print("\n No leads found.")
        return

    tiers: Dict[str, int] = {}
    industries: Dict[str, int] = {}

    for lead in leads:
        t = lead.get("lead_tier", "UNKNOWN")
        tiers[t] = tiers.get(t, 0) + 1
        ind = lead.get("industry", "Unknown")
        industries[ind] = industries.get(ind, 0) + 1

    print()
    print("=" * 55)
    print("  LEAD EXTRACTION SUMMARY")
    print("=" * 55)
    print(f"  Total leads extracted: {len(leads)}")
    print()

    tier_order = ["HOT", "WARM", "COOL", "COLD"]
    for tier in tier_order:
        count = tiers.get(tier, 0)
        if count:
            pct = count * 100 // len(leads)
            print(f"  {tier:8} : {count:4} ({pct:2}%)")

    print()
    print("  By industry:")
    for ind, count in sorted(industries.items(), key=lambda x: -x[1]):
        print(f"    {ind:35} : {count}")
    print("=" * 55)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Lead Extractor - Automated lead finding via Google Places API"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    parser.add_argument(
        "--output",
        default="leads_output/leads.csv",
        help="Output CSV path (default: leads_output/leads.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max leads to extract (0 = unlimited)",
    )
    parser.add_argument(
        "--google-key",
        help="Google Places API key (overrides GOOGLE_PLACES_API_KEY env var)",
    )
    parser.add_argument(
        "--hunter-key",
        help="Hunter.io API key (overrides HUNTER_API_KEY env var)",
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # API keys
    api_key = args.google_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        logger.error(
            "No Google Places API key found.\n"
            "  Set GOOGLE_PLACES_API_KEY environment variable or\n"
            "  pass --google-key <key>"
        )
        sys.exit(1)

    hunter_key = args.hunter_key or os.environ.get("HUNTER_API_KEY", "")
    if hunter_key:
        logger.info("Hunter.io email enrichment enabled")
    else:
        logger.info("No Hunter.io key set — skipping email enrichment")

    # Show config summary
    search_cfg = config.get("search", {})
    industries = [i["name"] for i in search_cfg.get("industries", [])]
    locations = [l["city"] for l in search_cfg.get("locations", [])]
    target = search_cfg.get("target_size", "micro")

    print()
    print("=" * 55)
    print("  LEAD EXTRACTOR PIPELINE")
    print("=" * 55)
    print(f"  Industries : {', '.join(industries)}")
    print(f"  Locations  : {len(locations)} cities across Chile")
    print(f"  Target     : {target} businesses (1-10 employees)")
    print(f"  Limit      : {'unlimited' if not args.limit else args.limit}")
    print()

    # Run
    leads = run_pipeline(config, api_key, hunter_key, args.limit)

    if not leads:
        logger.warning("No leads found. Try expanding keywords or locations.")
        sys.exit(0)

    export_csv(leads, args.output)
    print_summary(leads)

    return leads


if __name__ == "__main__":
    main()
