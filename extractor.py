"""
Google Places API client for automated business search.

Supports:
  - Text Search: keyword + location (used as default)
  - Nearby Search: lat/lng + radius + keyword (grid-based exploration)
  - Geocoding: city name → coordinates + viewport bounds
  - Grid generation: divide a city viewport into overlapping cells
"""

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

MAX_PAGES = 3
PAGE_TOKEN_DELAY = 3  # seconds — pagetokens need time to activate on Google's side
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5  # seconds multiplier

# -- Geocoding constants --
LAT_PER_M = 1.0 / 111_320.0
DEFAULT_GRID_RADIUS = 1500       # meters per cell
DEFAULT_GRID_OVERLAP = 0.2       # 20% overlap between adjacent cells
MAX_NEARBY_RADIUS = 50_000       # 50km = Google's max


@dataclass
class Bounds:
    """Rectangular viewport bounds."""
    south: float
    west: float
    north: float
    east: float

    @property
    def center(self) -> tuple[float, float]:
        return ((self.south + self.north) / 2, (self.west + self.east) / 2)

    @property
    def lat_span(self) -> float:
        return self.north - self.south

    @property
    def lng_span(self) -> float:
        return self.east - self.west

    @property
    def width_m(self) -> float:
        """Approximate width in meters at the center latitude."""
        mid_lat = self.center[0]
        return self.lng_span * 111_320.0 * math.cos(math.radians(mid_lat))

    @property
    def height_m(self) -> float:
        """Approximate height in meters."""
        return self.lat_span * 111_320.0


def lng_per_m_at(lat: float) -> float:
    """Longitude degrees per meter at a given latitude."""
    return 1.0 / (111_320.0 * math.cos(math.radians(lat)))


class PlacesExtractor:
    """Search for businesses using Google Places API.

    Uses Text Search to find businesses matching keywords + location,
    then fetches Place Details for phone, website, and other metadata.
    Also supports Nearby Search with grid-based city exploration.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    FIELDS = "website,formatted_phone_number,international_phone_number,opening_hours,url,rating,user_ratings_total"

    def __init__(self, api_key: str, session: aiohttp.ClientSession, config: dict | None = None):
        self.api_key = api_key
        self.session = session
        self._request_count = 0
        self._sem = asyncio.Semaphore(5)
        ext_cfg = (config or {}).get("extraction", {})
        self.max_pages = ext_cfg.get("max_pages", MAX_PAGES)
        self.page_token_delay = ext_cfg.get("page_token_delay", PAGE_TOKEN_DELAY)
        self.request_timeout = ext_cfg.get("request_timeout", REQUEST_TIMEOUT)
        self.max_retries = ext_cfg.get("max_retries", MAX_RETRIES)
        self.retry_backoff = ext_cfg.get("retry_backoff", RETRY_BACKOFF)

    async def _fetch_with_retry(self, url: str, params: dict, allow_redirects: bool = True) -> dict:
        """GET with exponential backoff on transient errors."""
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            async with self._sem:
                try:
                    async with self.session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.request_timeout),
                        allow_redirects=allow_redirects,
                    ) as resp:
                        return await resp.json()  # type: ignore[no-any-return]
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_error = e
                    if attempt < self.max_retries - 1:
                        delay = self.retry_backoff**attempt
                        logger.debug(
                            "Retry %d/%d in %.1fs: %s", attempt + 1, self.max_retries, delay, e
                        )
                        await asyncio.sleep(delay)
        assert last_error is not None
        raise last_error

    @property
    def request_count(self) -> int:
        return self._request_count

    async def search_businesses(self, keyword: str, location: str) -> list[dict]:
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
            logger.debug("Places API request page %d: %s", pages + 1, {k: v for k, v in params.items() if k != "key"})
            try:
                data = await self._fetch_with_retry(f"{self.BASE_URL}/textsearch/json", params)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error("Search failed: %s", e)
                break

            logger.debug("Places API response status: %s", data.get("status"))
            if data.get("status") != "OK":
                if data.get("status") == "ZERO_RESULTS":
                    logger.info("No results for '%s' in %s", keyword, location)
                    break

                # INVALID_REQUEST with pagetoken = token not ready yet. Retry with backoff.
                if data.get("status") == "INVALID_REQUEST" and "pagetoken" in params:
                    retry_delay = self.page_token_delay * (pages + 1)
                    logger.debug(
                        "Pagetoken not ready, waiting %ds (attempt %d)",
                        retry_delay, pages + 1,
                    )
                    await asyncio.sleep(retry_delay)
                    try:
                        data = await self._fetch_with_retry(
                            f"{self.BASE_URL}/textsearch/json", params
                        )
                        if data.get("status") == "OK":
                            logger.info("Pagetoken retry succeeded")
                            # fall through to process results below
                        else:
                            logger.warning(
                                "Pagetoken retry also failed: %s", data.get("status")
                            )
                            break
                    except (aiohttp.ClientError, asyncio.TimeoutError):
                        logger.warning("Pagetoken retry request failed")
                        break
                else:
                    logger.warning(
                        "Places API error: %s — %s (params: %s)",
                        data.get("status"),
                        data.get("error_message", "no details"),
                        {k: v for k, v in params.items() if k != "key"},
                    )
                    break

            # Collect place_ids for parallel detail fetch
            batch_ids = []
            for place in data.get("results", []):
                place_id = place.get("place_id")
                if not place_id or place_id in seen_place_ids:
                    continue
                seen_place_ids.add(place_id)
                batch_ids.append(place_id)

            # Fetch details in parallel for this batch
            if batch_ids:
                detail_tasks = [self._get_place_details(pid) for pid in batch_ids]
                details_list = await asyncio.gather(*detail_tasks, return_exceptions=True)

                for idx, place_id in enumerate(batch_ids):
                    place = next(
                        (p for p in data.get("results", []) if p.get("place_id") == place_id), {}
                    )
                    if not place:
                        continue

                    details = (
                        details_list[idx] if not isinstance(details_list[idx], Exception) else {}
                    )

                    results.append(
                        {
                            "place_id": place_id,
                            "business_name": place.get("name", ""),  # type: ignore[call-overload]
                            "address": place.get("formatted_address", ""),  # type: ignore[call-overload]
                            "rating": place.get("rating"),  # type: ignore[call-overload]
                            "total_ratings": place.get("user_ratings_total", 0),  # type: ignore[call-overload]
                            "types": place.get("types", []),  # type: ignore[call-overload]
                            "website": details.get("website", ""),  # type: ignore[union-attr]
                            "phone": details.get("formatted_phone_number", ""),  # type: ignore[union-attr]
                            "international_phone": details.get("international_phone_number", ""),  # type: ignore[union-attr]
                            "google_maps_url": details.get("url", ""),  # type: ignore[union-attr]
                            "source": "Google Maps",
                            "date_found": datetime.now().strftime("%Y-%m-%d"),
                        }
                    )

            next_token = data.get("next_page_token")
            if not next_token:
                break

            # Google Places requires ONLY pagetoken + key on subsequent pages
            params = {"pagetoken": next_token, "key": self.api_key}
            await asyncio.sleep(self.page_token_delay)
            pages += 1

        return results

    # ──────────────────────────────────────────────
    # Geocoding & Nearby Search (grid-based)
    # ──────────────────────────────────────────────

    async def geocode_city(self, city_name: str) -> Bounds | None:
        """Convert a city name to its viewport bounds via Google Geocoding API.

        Args:
            city_name: e.g. "Santiago, Chile" or "Ñuñoa"

        Returns:
            Bounds(south, west, north, east) or None if not found.
        """
        params = {
            "address": city_name,
            "key": self.api_key,
            "language": "es",
            "region": "cl",
        }
        try:
            data = await self._fetch_with_retry(self.GEOCODE_URL, params)
        except Exception as e:
            logger.error("Geocoding failed for '%s': %s", city_name, e)
            return None

        if data.get("status") != "OK" or not data.get("results"):
            logger.warning("Geocode status %s for '%s'", data.get("status"), city_name)
            return None

        viewport = data["results"][0]["geometry"].get("viewport")
        if not viewport:
            # Fallback: bounds or location
            loc = data["results"][0]["geometry"].get("location")
            if not loc:
                return None
            # Create a ~10km viewport around location
            return Bounds(
                south=loc["lat"] - 0.05,
                west=loc["lng"] - 0.05,
                north=loc["lat"] + 0.05,
                east=loc["lng"] + 0.05,
            )

        return Bounds(
            south=viewport["southwest"]["lat"],
            west=viewport["southwest"]["lng"],
            north=viewport["northeast"]["lat"],
            east=viewport["northeast"]["lng"],
        )

    async def nearby_search(
        self,
        keyword: str,
        lat: float,
        lng: float,
        radius: int = 1500,
    ) -> list[dict]:
        """Search businesses near a specific point using Places Nearby Search.

        Returns lead dicts (same schema as search_businesses).
        """
        results: list[dict] = []
        seen_place_ids: set[str] = set()

        params: dict = {
            "location": f"{lat},{lng}",
            "radius": str(radius),
            "keyword": keyword,
            "key": self.api_key,
            "language": "es",
        }

        pages = 0
        while pages < self.max_pages:
            data = await self._fetch_with_retry(f"{self.BASE_URL}/nearbysearch/json", params)

            if data.get("status") != "OK":
                if data.get("status") == "ZERO_RESULTS":
                    break
                if data.get("status") == "INVALID_REQUEST" and "pagetoken" in params:
                    await asyncio.sleep(self.page_token_delay * (pages + 1))
                    data = await self._fetch_with_retry(
                        f"{self.BASE_URL}/nearbysearch/json", params
                    )
                    if data.get("status") != "OK":
                        break
                else:
                    logger.debug(
                        "NearbySearch %s @ (%.4f,%.4f): %s",
                        keyword, lat, lng, data.get("status"),
                    )
                    break

            batch_ids = []
            for place in data.get("results", []):
                pid = place.get("place_id")
                if not pid or pid in seen_place_ids:
                    continue
                seen_place_ids.add(pid)
                batch_ids.append(pid)

            if batch_ids:
                detail_tasks = [self._get_place_details(pid) for pid in batch_ids]
                details_list = await asyncio.gather(*detail_tasks, return_exceptions=True)

                for idx, pid in enumerate(batch_ids):
                    place = next(
                        (p for p in data.get("results", []) if p.get("place_id") == pid), {}
                    )
                    if not place:
                        continue
                    details = (
                        details_list[idx] if not isinstance(details_list[idx], Exception) else {}
                    )
                    results.append(self._place_to_lead(place, details))

            next_token = data.get("next_page_token")
            if not next_token:
                break
            params = {"pagetoken": next_token, "key": self.api_key}
            await asyncio.sleep(self.page_token_delay)
            pages += 1

        return results

    # ──────────────────────────────────────────────
    # Grid search (city-wide)
    # ──────────────────────────────────────────────

    @staticmethod
    def generate_grid(
        bounds: Bounds,
        radius_m: int = DEFAULT_GRID_RADIUS,
        overlap: float = DEFAULT_GRID_OVERLAP,
    ) -> list[tuple[float, float]]:
        """Generate overlapping grid cell centers within city bounds.

        Each cell center is (lat, lng). Adjacent cells overlap by
        ``overlap`` fraction so that businesses near cell boundaries
        don't fall through the cracks.

        Returns:
            List of (lat, lng) cell centers.
        """
        mid_lat = bounds.center[0]
        step_deg_lat = 2 * radius_m * (1 - overlap) * LAT_PER_M
        step_deg_lng = 2 * radius_m * (1 - overlap) * lng_per_m_at(mid_lat)

        if step_deg_lat <= 0 or step_deg_lng <= 0:
            return [(bounds.center[0], bounds.center[1])]

        cells: list[tuple[float, float]] = []
        lat = bounds.south
        while lat < bounds.north:
            lng = bounds.west
            while lng < bounds.east:
                cells.append((lat, lng))
                lng += step_deg_lng
            lat += step_deg_lat
        return cells

    async def search_with_grid(
        self,
        keyword: str,
        city_name: str,
        radius_m: int = DEFAULT_GRID_RADIUS,
        overlap: float = DEFAULT_GRID_OVERLAP,
        cell_limit: int = 50,
    ) -> list[dict]:
        """Search an entire city using a grid of Nearby Search calls.

        1. Geocode the city name → viewport bounds
        2. Generate overlapping grid cells
        3. Run Nearby Search on each cell in parallel (throttled)
        4. Deduplicate across cells by place_id

        Args:
            keyword: Business type keyword (e.g. "barbería")
            city_name: City to explore (e.g. "Ñuñoa")
            radius_m: Search radius per cell (default 1500m)
            overlap: Fractional overlap between cells (default 20%)
            cell_limit: Max cells to search (safety cap)

        Returns:
            Combined deduplicated lead list.
        """
        bounds = await self.geocode_city(city_name)
        if not bounds:
            logger.error("Could not geocode city '%s'", city_name)
            return []

        cells = self.generate_grid(bounds, radius_m, overlap)
        if not cells:
            return []

        logger.info(
            "Grid search for '%s' in %s: %d cells, %.1fkm² area",
            keyword, city_name, len(cells),
            bounds.width_m * bounds.height_m / 1_000_000,
        )

        if len(cells) > cell_limit:
            logger.info(
                "Capping from %d to %d cells (use --cell-limit to adjust)",
                len(cells), cell_limit,
            )
            cells = cells[:cell_limit]

        # Search cells with bounded concurrency
        sem = asyncio.Semaphore(5)
        async def _search_one(lat: float, lng: float) -> list[dict]:
            async with sem:
                return await self.nearby_search(keyword, lat, lng, radius_m)

        tasks = [_search_one(lat, lng) for lat, lng in cells]
        cell_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Deduplicate by place_id
        seen: set[str] = set()
        all_leads: list[dict] = []
        for result in cell_results:
            if isinstance(result, Exception):
                continue
            for lead in result:
                pid = lead.get("place_id", "")
                if pid and pid not in seen:
                    seen.add(pid)
                    all_leads.append(lead)

        logger.info(
            "Grid search complete: %d unique leads from %d cells",
            len(all_leads), len(cells),
        )
        return all_leads

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _place_to_lead(self, place: dict, details: dict) -> dict:
        """Normalise a Places API result + details into a standard lead dict."""
        return {
            "place_id": place.get("place_id", ""),
            "business_name": place.get("name", ""),
            "address": place.get("vicinity") or place.get("formatted_address", ""),
            "rating": place.get("rating"),
            "total_ratings": place.get("user_ratings_total", 0),
            "types": place.get("types", []),
            "website": details.get("website", ""),
            "phone": details.get("formatted_phone_number", ""),
            "international_phone": details.get("international_phone_number", ""),
            "google_maps_url": details.get("url", ""),
            "source": "Google Maps",
            "date_found": datetime.now().strftime("%Y-%m-%d"),
        }

    async def _get_place_details(self, place_id: str) -> dict:
        """Fetch detailed information for a specific place."""
        params = {
            "place_id": place_id,
            "key": self.api_key,
            "fields": self.FIELDS,
            "language": "es",
        }
        try:
            data = await self._fetch_with_retry(f"{self.BASE_URL}/details/json", params)
            return data.get("result", {})  # type: ignore[no-any-return]
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error("Place details failed for %s: %s", place_id, e)
            return {}
