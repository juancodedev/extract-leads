#!/usr/bin/env python3
"""
Lead extraction pipeline core.

Contains only run_pipeline() — the pure extraction logic.
CLI, config loading, and output functions live in sibling modules.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List

from rapidfuzz import fuzz

from extractor import PlacesExtractor
from enricher import Enricher
from lead_scorer import LeadScorer
from analyzer import WebsiteAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DUP_THRESHOLD = 85


def deduplicate_leads(leads: List[Dict], threshold: int = DUP_THRESHOLD) -> List[Dict]:
    """Fuzzy-deduplicate leads by business name, keeping highest-scored lead."""
    seen = []
    unique = []
    for lead in sorted(leads, key=lambda x: x.get("lead_score", 0), reverse=True):
        name = (lead.get("business_name") or "").lower()
        is_dup = False
        for existing in seen:
            if fuzz.token_sort_ratio(name, existing) >= threshold:
                is_dup = True
                break
        if not is_dup:
            seen.append(name)
            unique.append(lead)
    return unique


def run_pipeline(
    config: Dict,
    api_key: str,
    hunter_key: str = "",
    limit: int = 0,
    goal: str = "general",
    do_seo: bool = False,
    do_ads: bool = False,
    do_ig_web: bool = False,
) -> List[Dict]:
    """Execute the full extraction pipeline with optional deep audits."""
    extractor = PlacesExtractor(api_key)
    enricher = Enricher(hunter_key if hunter_key else None)
    scorer = LeadScorer(config, goal=goal)
    analyzer = WebsiteAnalyzer() if do_seo else None

    all_leads: List[Dict] = []
    seen_names: set = set()

    search_config = config.get("search", {})
    industries = search_config.get("industries", [])
    locations = search_config.get("locations", [])

    # Distribute limit across industries for balanced results
    per_industry_limit = 0
    if limit:
        per_industry_limit = limit // len(industries) if industries else limit

    total_combos = len(industries) * len(locations)
    done = 0

    for industry in industries:
        industry_leads = 0

        for keyword in industry.get("keywords", []):
            for loc in locations:
                if per_industry_limit and industry_leads >= per_industry_limit:
                    break
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
                        "whatsapp_link": "",
                        "booking_links": "",
                        "whatsapp_phone": "",
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

                    # Scan website for social, WhatsApp, booking links
                    if lead["website"]:
                        scan = enricher.scan_website(lead["website"], name)
                        lead["facebook_url"] = scan.get("facebook") or ""
                        ig = scan.get("instagram") or ""
                        lead["instagram_handle"] = f"@{ig}" if ig and not ig.startswith("@") else ig
                        lead["linkedin_url"] = scan.get("linkedin") or ""
                        lead["whatsapp_link"] = scan.get("whatsapp") or ""
                        booking = scan.get("booking_links", [])
                        lead["booking_links"] = " | ".join(booking) if booking else ""

                    # Generate WhatsApp link from phone as fallback
                    if not lead["whatsapp_link"] and lead["phone"]:
                        clean = re.sub(r"[^\d+]", "", lead["phone"])
                        if clean.startswith("+"):
                            lead["whatsapp_link"] = f"https://wa.me/{clean[1:]}"
                        else:
                            lead["whatsapp_link"] = f"https://wa.me/{clean}"
                    if lead["whatsapp_link"]:
                        lead["whatsapp_phone"] = lead["phone"]

                    # Scoring
                    lead = scorer.score(lead)
                    all_leads.append(lead)
                    industry_leads += 1

                    if limit and len(all_leads) >= limit:
                        break

            if limit and len(all_leads) >= limit:
                break

        if per_industry_limit and industry_leads >= per_industry_limit:
            logger.info(
                "Reached %d leads for '%s', moving to next industry",
                industry_leads, industry.get("name"),
            )

    # --- DEEP AUDITS FOR TOP LEADS ---
    if all_leads and (do_seo or do_ads or do_ig_web):
        # Sort by score and take top 10 for deep audit
        top_for_audit = sorted(all_leads, key=lambda x: x.get("lead_score", 0), reverse=True)[:10]
        logger.info("Realizando auditorías profundas para los top 10 prospectos...")

        for lead in top_for_audit:
            # 1. SEO Audit
            if do_seo and lead.get("website") and analyzer:
                logger.info("  Auditando SEO: %s", lead["business_name"])
                try:
                    audit_data = analyzer.analyze(lead["website"])
                    lead["audit_data"] = audit_data
                    # Re-score with audit data
                    updated = scorer.score(lead)
                    lead.update(updated)
                except Exception as e:
                    logger.debug("Deep SEO audit failed for %s: %s", lead["business_name"], e)

            # 2. Meta Ads (Flag for Agent/User)
            if do_ads:
                lead["requires_ads_audit"] = True
            
            # 3. IG to Web (Flag for Agent/User)
            if do_ig_web and lead.get("instagram_handle"):
                lead["requires_ig_web_prototype"] = True

    all_leads = deduplicate_leads(all_leads)
    return all_leads


# ── Backward-compatible re-exports ──────────────────────────────────
# NOTE: cli's main/run_interactive are NOT imported at module level
# to avoid circular import (cli imports run_pipeline from here).
# They are resolved lazily via __getattr__.
from config_loader import load_config          # noqa: E402, F401
from exporters import export_csv, load_leads_from_csv  # noqa: E402, F401
from reporters import print_summary, export_html       # noqa: E402, F401


def __getattr__(name):
    """Lazy re-exports for cli.py symbols to break circular import."""
    if name in ("main", "run_interactive"):
        import cli as _cli
        return getattr(_cli, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    from cli import main as _main
    _main()
