"""
Proactive Instagram profile search for leads.

Searches Instagram's public topsearch endpoint to find business
Instagram handles by business name + city.  No authentication
required — uses the same endpoint Instagram's own search box does.
"""

import asyncio
import logging
import re
from typing import Any

import aiohttp
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# ── Config ──

TOPSEARCH_URL = "https://www.instagram.com/web/search/topsearch/?query={query}"
REQUEST_TIMEOUT = 10
MAX_RETRIES = 2
FUZZY_THRESHOLD = 70  # minimum similarity to consider a match
MIN_HANDLE_LENGTH = 3
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def _clean_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    name = re.sub(r"[^\w\s]", " ", name.lower())
    return re.sub(r"\s+", " ", name).strip()


def _rank_candidates(
    candidates: list[dict[str, Any]],
    business_name: str,
) -> list[dict[str, Any]]:
    """Rank Instagram user candidates by name similarity + followers.

    Returns candidates sorted descending by combined score.
    """
    clean_biz = _clean_name(business_name)
    scored: list[tuple[float, dict]] = []

    for c in candidates:
        username = c.get("user", {}).get("username", "")
        full_name = c.get("user", {}).get("full_name", "")
        follower_count = c.get("user", {}).get("follower_count", 0)
        is_verified = c.get("user", {}).get("is_verified", False)

        # Score based on fuzzy match of both username and full_name
        score = max(
            fuzz.token_sort_ratio(clean_biz, _clean_name(username)),
            fuzz.token_sort_ratio(clean_biz, _clean_name(full_name)),
        )

        # Boost verified + high-follower accounts (more likely to be the real business)
        if is_verified:
            score += 20
        if follower_count > 1000:
            score += 10
        elif follower_count > 100:
            score += 5

        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored]


async def search_instagram_profile(
    session: aiohttp.ClientSession,
    business_name: str,
    location: str = "",
) -> str:
    """Search Instagram for a business profile by name + optional location.

    Returns the Instagram handle (e.g. ``"@peluqueria_x"``) or empty string
    if no good match is found.
    """
    # Build search query
    query_parts = [business_name]
    if location:
        # Take just the city name (before comma)
        city = location.split(",")[0].strip()
        if city:
            query_parts.append(city)
    query = " ".join(query_parts)

    # Try Instagram topsearch API
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
            "Referer": "https://www.instagram.com/",
            "X-Requested-With": "XMLHttpRequest",
        }

        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(
                    TOPSEARCH_URL.format(query=query),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    allow_redirects=True,
                ) as resp:
                    if resp.status != 200:
                        logger.debug(
                            "Instagram topsearch returned %d for '%s'",
                            resp.status, query,
                        )
                        await asyncio.sleep(1)
                        continue

                    data: dict = await resp.json()
                    break
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.debug("Instagram search attempt %d failed: %s", attempt + 1, e)
                if attempt == MAX_RETRIES - 1:
                    return ""
                await asyncio.sleep(1)
        else:
            return ""

        users: list[dict] = data.get("users", [])
        if not users:
            logger.debug("No Instagram users found for '%s'", query)
            return ""

        candidates = _rank_candidates(users, business_name)
        best = candidates[0]
        best_score = max(
            fuzz.token_sort_ratio(_clean_name(business_name), _clean_name(
                best.get("user", {}).get("username", "")
            )),
            fuzz.token_sort_ratio(_clean_name(business_name), _clean_name(
                best.get("user", {}).get("full_name", "")
            )),
        )

        if best_score < FUZZY_THRESHOLD:
            logger.debug(
                "Best Instagram match for '%s' scored %d (threshold: %d): @%s (%s)",
                business_name, best_score, FUZZY_THRESHOLD,
                best.get("user", {}).get("username", ""),
                best.get("user", {}).get("full_name", ""),
            )
            return ""

        handle = best.get("user", {}).get("username", "")
        if len(handle) < MIN_HANDLE_LENGTH:
            return ""

        logger.info(
            "Instagram match: %s → @%s (score: %d, followers: %d)",
            business_name, handle, best_score,
            best.get("user", {}).get("follower_count", 0),
        )
        return f"@{handle}"

    except Exception as e:
        logger.debug("Instagram search exception for '%s': %s", query, e)
        return ""
