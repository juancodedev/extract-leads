"""
Email and social media enrichment for leads.
"""
import logging
import re
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class Enricher:
    """Enrich leads with emails (via Hunter.io) and social media links.

    Hunter.io API: https://hunter.io/api/v2/domain-search
    Social detection: parses website HTML for known social URLs.
    """

    def __init__(self, hunter_api_key: Optional[str] = None):
        self.hunter_api_key = hunter_api_key

    def find_email(self, domain: str) -> Optional[str]:
        """Find email address for a domain using Hunter.io."""
        if not self.hunter_api_key or not domain:
            return None

        url = "https://api.hunter.io/v2/domain-search"
        params = {"domain": domain, "api_key": self.hunter_api_key}

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            emails = data.get("data", {}).get("emails", [])
            if emails:
                for email in emails:
                    if email.get("value"):
                        return email["value"]
        except requests.RequestException as e:
            logger.debug("Hunter.io lookup failed for %s: %s", domain, e)

        return None

    def detect_social(self, website: str, business_name: str = "") -> Dict[str, Optional[str]]:
        """Scan website HTML for social media links.

        Searches in HTML, JSON-LD structured data, and common CMS patterns.
        Returns dict with facebook, instagram, linkedin keys.
        """
        social = {"facebook": None, "instagram": None, "linkedin": None}
        if not website:
            return social

        if not website.startswith("http"):
            website = "https://" + website

        try:
            resp = requests.get(
                website,
                timeout=10,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )
            html = resp.text

            # Facebook patterns
            fb_patterns = [
                r'(?:facebook\.com|fb\.com)/([a-zA-Z0-9._-]+)',
                r'"fb:page_url"\s*:\s*"([^"]+)"',
                r'"facebook"\s*:\s*"([^"]+)"',
            ]
            for p in fb_patterns:
                m = re.search(p, html)
                if m:
                    val = m.group(1)
                    if val and val not in ("share.php", "sharer", "plugins"):
                        social["facebook"] = val if "facebook.com" in val else f"facebook.com/{val}"
                        break

            # Instagram patterns
            ig_patterns = [
                r'instagram\.com/([a-zA-Z0-9._-]+)',
                r'"instagram"\s*:\s*"([^"]+)"',
                r'"instagram_handle"\s*:\s*"([^"]+)"',
            ]
            for p in ig_patterns:
                m = re.search(p, html)
                if m:
                    val = m.group(1)
                    if val and val not in ("p", "explore", "accounts", "developer", "about"):
                        social["instagram"] = f"@{val}" if not val.startswith("@") else val
                        break

            # LinkedIn patterns
            li_patterns = [
                r'linkedin\.com/(?:company|in)/([a-zA-Z0-9._-]+)',
                r'"linkedin"\s*:\s*"([^"]+)"',
            ]
            for p in li_patterns:
                m = re.search(p, html)
                if m:
                    social["linkedin"] = f"linkedin.com/{m.group(1)}"
                    break

            # Try JSON-LD structured data as fallback
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
                            social["facebook"] = u
                        elif "instagram.com" in u_lower:
                            social["instagram"] = f"@{u.split('/')[-1]}"
                        elif "linkedin.com" in u_lower:
                            social["linkedin"] = u

        except requests.RequestException as e:
            logger.debug("Social detection failed for %s: %s", website, e)

        return social

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
