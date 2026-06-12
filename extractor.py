"""
Google Places API client for automated business search.
"""
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

MAX_PAGES = 3
PAGE_TOKEN_DELAY = 2  # seconds
REQUEST_TIMEOUT = 15  # seconds


class PlacesExtractor:
    """Search for businesses using Google Places API.

    Uses Text Search to find businesses matching keywords + location,
    then fetches Place Details for phone, website, and other metadata.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    FIELDS = "website,formatted_phone_number,international_phone_number,opening_hours,url,rating,user_ratings_total"

    def __init__(self, api_key: str, config: Optional[Dict] = None):
        self.api_key = api_key
        self._request_count = 0
        ext_cfg = (config or {}).get("extraction", {})
        self.max_pages = ext_cfg.get("max_pages", MAX_PAGES)
        self.page_token_delay = ext_cfg.get("page_token_delay", PAGE_TOKEN_DELAY)
        self.request_timeout = ext_cfg.get("request_timeout", REQUEST_TIMEOUT)

    @property
    def request_count(self) -> int:
        return self._request_count

    def search_businesses(self, keyword: str, location: str) -> List[Dict]:
        """Search for businesses matching keyword near location.

        Args:
            keyword: Business type keyword (e.g., "barbería", "cafetería")
            location: City/location name (e.g., "Santiago, Chile")

        Returns:
            List of lead dicts with place data
        """
        results = []
        seen_place_ids = set()

        params = {
            "query": f"{keyword} en {location}",
            "key": self.api_key,
            "language": "es",
            "region": "cl",
        }

        pages = 0
        while pages < self.max_pages:
            resp = self._request("/textsearch/json", params)
            if resp is None:
                break

            data = resp.json()
            if data.get("status") != "OK":
                if data.get("status") == "ZERO_RESULTS":
                    break
                logger.warning(
                    "Places API error: %s - %s",
                    data.get("status"),
                    data.get("error_message", ""),
                )
                break

            for place in data.get("results", []):
                place_id = place.get("place_id")
                if not place_id or place_id in seen_place_ids:
                    continue
                seen_place_ids.add(place_id)

                details = self._get_place_details(place_id)

                results.append(
                    {
                        "place_id": place_id,
                        "business_name": place.get("name", ""),
                        "address": place.get("formatted_address", ""),
                        "rating": place.get("rating"),
                        "total_ratings": place.get("user_ratings_total", 0),
                        "types": place.get("types", []),
                        "website": details.get("website", ""),
                        "phone": details.get("formatted_phone_number", ""),
                        "international_phone": details.get(
                            "international_phone_number", ""
                        ),
                        "google_maps_url": details.get("url", ""),
                        "source": "Google Maps",
                        "date_found": datetime.now().strftime("%Y-%m-%d"),
                    }
                )

            next_token = data.get("next_page_token")
            if not next_token:
                break

            params["pagetoken"] = next_token
            time.sleep(self.page_token_delay)
            pages += 1

        return results

    def _get_place_details(self, place_id: str) -> Dict:
        """Fetch detailed information for a specific place."""
        params = {
            "place_id": place_id,
            "key": self.api_key,
            "fields": self.FIELDS,
            "language": "es",
        }
        resp = self._request("/details/json", params)
        if resp is None:
            return {}
        data = resp.json()
        return data.get("result", {})

    def _request(self, endpoint: str, params: Dict) -> Optional[requests.Response]:
        """Make a rate-limited request to the Places API."""
        self._request_count += 1
        try:
            resp = requests.get(
                f"{self.BASE_URL}{endpoint}",
                params=params,
                timeout=self.request_timeout,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.error("Request failed: %s", e)
            return None
