"""
Email and social media enrichment for leads.
"""
import asyncio
import logging
import re
from typing import Dict, Optional

import aiohttp

from booking_data import BOOKING_DOMAINS, BOOKING_SKIP

logger = logging.getLogger(__name__)

HUNTER_TIMEOUT = 10
WEBSITE_SCAN_TIMEOUT = 10
MIN_HANDLE_LENGTH = 3


class Enricher:
    """Enrich leads with emails (via Hunter.io) and social media links.

    Hunter.io API: https://hunter.io/api/v2/domain-search
    Social detection: parses website HTML for known social URLs.
    """

    def __init__(self, hunter_api_key: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None, config: Optional[Dict] = None):
        self.hunter_api_key = hunter_api_key
        self.session = session
        self._hunter_sem = asyncio.Semaphore(3)
        self._web_sem = asyncio.Semaphore(10)
        env_cfg = (config or {}).get("enrichment", {})
        self.hunter_timeout = env_cfg.get("hunter_timeout", HUNTER_TIMEOUT)
        self.website_scan_timeout = env_cfg.get("website_scan_timeout", WEBSITE_SCAN_TIMEOUT)

    async def find_email(self, domain: str) -> Optional[str]:
        """Find email address for a domain using Hunter.io."""
        if not self.hunter_api_key or not domain or not self.session:
            return None

        url = "https://api.hunter.io/v2/domain-search"
        params = {"domain": domain, "api_key": self.hunter_api_key}

        async with self._hunter_sem:
            try:
                async with self.session.get(
                    url, params=params,
                    timeout=aiohttp.ClientTimeout(total=self.hunter_timeout),
                ) as resp:
                    data = await resp.json()
                    emails = data.get("data", {}).get("emails", [])
                    if emails:
                        for email in emails:
                            if email.get("value"):
                                return email["value"]
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.debug("Hunter.io lookup failed for %s: %s", domain, e)

        return None

    async def scan_website(self, website: str, business_name: str = "") -> Dict[str, Optional[str]]:
        """Scan website HTML for social media, WhatsApp, and booking links.

        Returns dict with: facebook, instagram, linkedin, whatsapp, booking_links.
        """
        result = {
            "facebook": None,
            "instagram": None,
            "linkedin": None,
            "whatsapp": None,
            "booking_links": [],
        }
        if not website or not self.session:
            return result

        if not website.startswith("http"):
            website = "https://" + website

        async with self._web_sem:
            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                async with self.session.get(
                    website,
                    timeout=aiohttp.ClientTimeout(total=self.website_scan_timeout),
                    headers=headers,
                ) as resp:
                    html = await resp.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.debug("Website scan failed for %s: %s", website, e)
                return result

            # ── Facebook ──
            fb_skip = {"share.php", "sharer", "plugins", "tr", "track", "events"}
            fb_patterns = [
                r'(?:facebook\.com|fb\.com)/([a-zA-Z0-9._-]+)',
                r'"fb:page_url"\s*:\s*"([^"]+)"',
                r'"facebook"\s*:\s*"([^"]+)"',
            ]
            for p in fb_patterns:
                m = re.search(p, html)
                if m:
                    val = m.group(1)
                    if val and val not in fb_skip and len(val) > MIN_HANDLE_LENGTH:
                        result["facebook"] = val if "facebook.com" in val else f"facebook.com/{val}"
                        break

            # ── Instagram ──
            ig_skip = {"p", "explore", "accounts", "developer", "about",
                       "rsrc.php", "static", "help", "legal", "terms"}
            ig_patterns = [
                r'instagram\.com/([a-zA-Z0-9._-]+)',
                r'"instagram"\s*:\s*"([^"]+)"',
                r'"instagram_handle"\s*:\s*"([^"]+)"',
            ]
            for p in ig_patterns:
                m = re.search(p, html)
                if m:
                    val = m.group(1)
                    if val and val not in ig_skip and len(val) > MIN_HANDLE_LENGTH:
                        result["instagram"] = val if not val.startswith("@") else val
                        break

            # ── LinkedIn ──
            li_patterns = [
                r'linkedin\.com/(?:company|in)/([a-zA-Z0-9._-]+)',
                r'"linkedin"\s*:\s*"([^"]+)"',
            ]
            for p in li_patterns:
                m = re.search(p, html)
                if m:
                    result["linkedin"] = f"linkedin.com/{m.group(1)}"
                    break

            # ── WhatsApp ──
            wa_patterns = [
                r'wa\.me/(\d+)',
                r'api\.whatsapp\.com/send\?phone=(\d+)',
                r'whatsapp\.com/send\?phone=(\d+)',
                r'whatsapp\.com/c/([a-zA-Z0-9_-]+)',
            ]
            for p in wa_patterns:
                m = re.search(p, html)
                if m:
                    phone = re.sub(r"\D", "", m.group(1))
                    result["whatsapp"] = f"https://wa.me/{phone}"
                    break

            # ── Booking/Reservation Systems ──
            seen_bookings = set()
            for domain in BOOKING_DOMAINS.keys():
                for m in re.finditer(
                    r'https?://[^"\'<> ]*' + re.escape(domain) + r'[^"\'<> ]*',
                    html,
                ):
                    url = m.group(0)
                    url_lower = url.lower()
                    if any(skip in url_lower for skip in BOOKING_SKIP):
                        continue
                    if url not in seen_bookings:
                        seen_bookings.add(url)
                        result["booking_links"].append(url)

            # ── JSON-LD structured data ──
            json_lds = re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                html,
                re.DOTALL,
            )
            for jd in json_lds:
                same_as_match = re.search(r'"sameAs"\s*:\s*\[(.*?)\]', jd)
                if same_as_match:
                    urls = re.findall(r'"([^"]+)"', same_as_match.group(1))
                    for u in urls:
                        u_lower = u.lower()
                        if "facebook.com" in u_lower:
                            result["facebook"] = u
                        elif "instagram.com" in u_lower:
                            result["instagram"] = u.split("/")[-1]
                        elif "linkedin.com" in u_lower:
                            result["linkedin"] = u

        return result

    @staticmethod
    def extract_domain(website: str) -> Optional[str]:
        """Extract clean domain from a URL."""
        if not website:
            return None
        website = website.strip().lower()
        website = re.sub(r"^https?://(www\d?\.)?", "", website)
        website = website.split("/")[0]
        website = website.split("?")[0]
        return website if website else None
