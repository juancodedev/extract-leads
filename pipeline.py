#!/usr/bin/env python3
"""
Lead extraction pipeline core.

Contains only run_pipeline() — the pure extraction logic.
CLI, config loading, and output functions live in sibling modules.
"""

import asyncio
import logging
import math
import re
from datetime import datetime

import aiohttp
from rapidfuzz import fuzz
from tqdm import tqdm

from analyzer import WebsiteAnalyzer
from enricher import Enricher
from extractor import PlacesExtractor
from instagram_search import search_instagram_profile
from lead_scorer import LeadScorer

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DUP_THRESHOLD = 85


def deduplicate_leads(leads: list[dict], threshold: int = DUP_THRESHOLD) -> list[dict]:
    """Fuzzy-deduplicate leads by business name, keeping highest-scored lead."""
    seen: list[str] = []
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


async def run_pipeline(
    config: dict,
    api_key: str,
    hunter_key: str = "",
    limit: int = 0,
    goal: str = "general",
    do_seo: bool = False,
    do_ads: bool = False,
    do_ig_web: bool = False,
    *,
    grid: bool = False,
    grid_radius: int = 1500,
    grid_overlap: float = 0.2,
    grid_cell_limit: int = 50,
) -> list[dict]:
    """Execute the full extraction pipeline with optional deep audits.

    Creates a single aiohttp.ClientSession and injects it into all
    HTTP-consuming modules for connection pooling and DNS caching.

    Args:
        grid: Use Nearby Search grid instead of Text Search (much more results).
        grid_radius: Search radius in meters per grid cell.
        grid_overlap: Fractional overlap between adjacent cells.
        grid_cell_limit: Max grid cells to search (safety cap).
    """
    connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        extractor = PlacesExtractor(api_key, session, config)
        enricher = Enricher(hunter_key, session, config)
        scorer = LeadScorer(config, goal=goal)
        analyzer = WebsiteAnalyzer(session, config=config) if do_seo else None

        all_leads: list[dict] = []
        seen_names: set = set()

        search_config = config.get("search", {})
        industries = search_config.get("industries", [])
        locations = search_config.get("locations", [])

        per_industry_limit = 0
        if limit:
            per_industry_limit = math.ceil(limit / len(industries)) if industries else limit

        total_combos = len(industries) * len(locations)
        pbar = tqdm(total=total_combos, desc="Extracting", unit="combo") if total_combos else None

        for industry in industries:
            industry_leads = 0
            for keyword in industry.get("keywords", []):
                for loc in locations:
                    if per_industry_limit and industry_leads >= per_industry_limit:
                        break
                    if limit and len(all_leads) >= limit:
                        break

                    if pbar:
                        pbar.set_postfix_str(f"{keyword} @ {loc['city']}")

                    try:
                        if grid:
                            # Grid-based Nearby Search (much more coverage)
                            results = await extractor.search_with_grid(
                                keyword,
                                f"{loc['city']}, {loc['region']}",
                                radius_m=grid_radius,
                                overlap=grid_overlap,
                                cell_limit=grid_cell_limit,
                            )
                        else:
                            # Standard Text Search
                            results = await extractor.search_businesses(
                                keyword, f"{loc['city']}, {loc['region']}"
                            )
                    except Exception as e:
                        logger.error("Search failed: %s", e)
                        continue

                    lead_batch = []
                    for place in results:
                        name = place.get("business_name", "")
                        if not name or name.lower() in seen_names:
                            continue
                        seen_names.add(name.lower())

                        industry_name = LeadScorer.classify_industry(
                            place.get("types", []), name, config
                        )

                        lead = {
                            "business_name": name,
                            "industry": industry_name,
                            "contact_person": "",
                            "phone": place.get("international_phone") or place.get("phone", ""),
                            "email": "",
                            "address": place.get("address", ""),
                            "city": LeadScorer.extract_city(place.get("address", ""), config),
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
                        lead_batch.append(lead)

                    # Enrich all leads in this batch in parallel
                    if lead_batch:
                        enrich_tasks = [
                            _enrich_lead(lead, enricher, session, hunter_key)
                            for lead in lead_batch
                        ]
                        enriched = await asyncio.gather(*enrich_tasks, return_exceptions=True)

                        for lead, result in zip(lead_batch, enriched, strict=True):
                            if isinstance(result, Exception):
                                logger.debug(
                                    "Enrichment failed for %s: %s", lead["business_name"], result
                                )
                            else:
                                lead.update(result)  # type: ignore[arg-type]

                            lead = scorer.score(lead)
                            all_leads.append(lead)
                            industry_leads += 1

                    if pbar:
                        pbar.update(1)

                    if limit and len(all_leads) >= limit:
                        break
                if limit and len(all_leads) >= limit:
                    break
            if per_industry_limit and industry_leads >= per_industry_limit:
                logger.info(
                    "Reached %d leads for '%s', moving to next",
                    industry_leads,
                    industry.get("name"),
                )

        if pbar:
            pbar.close()

        # --- DEEP AUDITS ---
        if all_leads and (do_seo or do_ads or do_ig_web):
            top_for_audit = sorted(all_leads, key=lambda x: x.get("lead_score", 0), reverse=True)[
                :10
            ]
            logger.info("Realizando auditorías profundas para los top 10 prospectos...")

            if do_seo and analyzer:
                audit_tasks = []
                for lead in top_for_audit:
                    if lead.get("website"):
                        audit_tasks.append(_audit_lead(lead, analyzer, scorer))

                if audit_tasks:
                    audit_results = await asyncio.gather(*audit_tasks, return_exceptions=True)
                    for lead, result in zip(
                        [lead for lead in top_for_audit if lead.get("website")],
                        audit_results,
                        strict=True,
                    ):
                        if isinstance(result, Exception):
                            logger.debug("Audit failed for %s: %s", lead["business_name"], result)
                        else:
                            lead.update(result)  # type: ignore[arg-type]

            for lead in top_for_audit:
                if do_ads:
                    lead["requires_ads_audit"] = True
                if do_ig_web and lead.get("instagram_handle"):
                    lead["requires_ig_web_prototype"] = True

        dup_threshold = config.get("scoring", {}).get("dup_threshold", DUP_THRESHOLD)
        all_leads = deduplicate_leads(all_leads, threshold=dup_threshold)

    return all_leads


async def _enrich_lead(
    lead: dict,
    enricher: "Enricher",
    session: aiohttp.ClientSession,
    hunter_key: str,
) -> dict:
    """Enrich a single lead with email + website scan + proactive Instagram search."""
    updates = {}
    if lead["website"] and hunter_key:
        domain = Enricher.extract_domain(lead["website"])
        if domain:
            email = await enricher.find_email(domain)
            if email:
                updates["email"] = email

    if lead["website"]:
        scan = await enricher.scan_website(lead["website"])
        updates["facebook_url"] = scan.get("facebook") or ""
        ig = scan.get("instagram") or ""
        updates["instagram_handle"] = f"@{ig}" if ig and not ig.startswith("@") else ig
        updates["linkedin_url"] = scan.get("linkedin") or ""
        updates["whatsapp_link"] = scan.get("whatsapp") or ""
        booking: list[str] = scan.get("booking_links", [])
        updates["booking_links"] = " | ".join(booking) if booking else ""

    # Proactive Instagram search: if we didn't find one on the website, search by name + city
    if not updates.get("instagram_handle"):
        ig_handle = await search_instagram_profile(
            session,
            lead.get("business_name", ""),
            location=lead.get("city", ""),
        )
        if ig_handle:
            updates["instagram_handle"] = ig_handle

    # WhatsApp fallback from phone
    if not updates.get("whatsapp_link") and lead.get("phone"):
        clean = re.sub(r"[^\d+]", "", lead["phone"])
        if clean.startswith("+"):
            updates["whatsapp_link"] = f"https://wa.me/{clean[1:]}"
        else:
            updates["whatsapp_link"] = f"https://wa.me/{clean}"
    if updates.get("whatsapp_link"):
        updates["whatsapp_phone"] = lead["phone"]

    return updates


async def _audit_lead(lead: dict, analyzer: "WebsiteAnalyzer", scorer: "LeadScorer") -> dict:
    """Run SEO audit on a single lead."""
    try:
        audit_data = await analyzer.analyze(lead["website"])
        lead["audit_data"] = audit_data
        return scorer.score(lead)
    except Exception as e:
        logger.debug("SEO audit failed for %s: %s", lead["business_name"], e)
        return {}
