"""
Integration tests for the async extraction pipeline.

Uses pytest-asyncio and unittest.mock to simulate HTTP responses
from Google Places API, Hunter.io, and website scans without hitting
real network endpoints.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline import run_pipeline

# ── Mock helpers ───────────────────────────────────────────────────────


def _mock_context_manager(return_value):
    """Build a mock that supports `async with obj as var:` protocol.

    When `async with session.get(url) as resp:` is used, the return
    value of `session.get()` must support the async context manager
    protocol.  This helper wires up __aenter__/__aexit__ so the
    `resp` variable receives `return_value`.
    """
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=return_value)
    ctx.__aexit__ = AsyncMock(return_value=None)
    return ctx


def _make_get_side_effect(places_search, places_detail=None, hunter=None, geocode_response=None):
    """Closure that returns the right mock HTTP response based on URL.

    Parameters
    ----------
    places_search : dict
        Response body for the Places API nearbysearch endpoint.
    places_detail : dict | None
        Response body for the Places API details endpoint.
        Defaults to ``{"result": {}}``.
    hunter : dict | None
        Response body for the Hunter.io domain-search endpoint.
        Defaults to ``{"data": {"emails": []}}``.
    geocode_response : dict | None
        Response body for the Geocoding API endpoint.
        Defaults to a valid Santiago viewport with ``"status": "OK"``.
    """
    if places_detail is None:
        places_detail = {"result": {}}
    if hunter is None:
        hunter = {"data": {"emails": []}}
    if geocode_response is None:
        geocode_response = {
            "status": "OK",
            "results": [
                {
                    "geometry": {
                        "viewport": {
                            "southwest": {"lat": -33.45, "lng": -70.65},
                            "northeast": {"lat": -33.44, "lng": -70.64},
                        }
                    }
                }
            ],
        }

    def _get(*args, **kwargs):
        url = args[0]
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.url = url
        mock_resp.history = []
        mock_resp.headers = {}

        if "geocode" in url:
            mock_resp.json = AsyncMock(return_value=geocode_response)
        elif "nearbysearch" in url:
            mock_resp.json = AsyncMock(return_value=places_search)
        elif "details" in url:
            mock_resp.json = AsyncMock(return_value=places_detail)
        elif "hunter.io" in url:
            mock_resp.json = AsyncMock(return_value=hunter)
        else:
            # Website scan — return minimal empty HTML
            mock_resp.text = AsyncMock(return_value="<html><head></head><body></body></html>")
            mock_resp.json = AsyncMock(return_value={})

        return _mock_context_manager(mock_resp)

    return _get


def _build_mock_session(get_side_effect):
    """Create a mock ``aiohttp.ClientSession`` wired for async usage.

    The returned mock supports both ``async with ClientSession() as session``
    and ``session.get(...)`` calls via the provided side_effect.

    We use ``AsyncMock`` for the session itself (to support ``async with``)
    but explicitly set ``.get`` to a regular ``MagicMock`` with a sync
    ``side_effect``.  If ``.get`` were left as the default ``AsyncMock``
    child, ``session.get(url)`` would return a coroutine instead of a
    context-manager object, breaking ``async with session.get(...)``.
    """
    mock_session = AsyncMock()
    mock_session.get = MagicMock(side_effect=get_side_effect)
    # When entering `async with ClientSession() as session:`, the
    # `session` variable must be the same mock so `.get()` works.
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return mock_session


def _make_place(place_id, name, address, rating, ratings_total, types):
    """Shortcut to build a Places API textsearch result dict."""
    return {
        "place_id": place_id,
        "name": name,
        "formatted_address": address,
        "rating": rating,
        "user_ratings_total": ratings_total,
        "types": types,
    }


# ── Test 1: End-to-end extraction + scoring ──────────────────────────


@pytest.mark.asyncio
async def test_pipeline_extracts_and_scores_leads(base_config):
    """Two barber-shop results → 2 leads, scored, not deduped."""
    places_search = {
        "status": "OK",
        "results": [
            _make_place(
                "p1",
                "Barbería Test Uno",
                "Av. Siempre Viva 123, Santiago",
                4.5,
                10,
                ["barber_shop", "hair_care"],
            ),
            _make_place("p2", "Café Test Dos", "Calle Falsa 456, Santiago", 4.0, 5, ["cafe"]),
        ],
        "next_page_token": None,
    }
    places_detail = {
        "result": {
            "website": "https://barberia-test.cl",
            "formatted_phone_number": "+56912345678",
            "international_phone_number": "+56912345678",
            "url": "https://maps.google.com/test",
        }
    }

    mock_session = _build_mock_session(_make_get_side_effect(places_search, places_detail))

    with (
        patch("aiohttp.ClientSession", return_value=mock_session),
        patch("pipeline.tqdm", MagicMock()),
    ):
        leads = await run_pipeline(base_config, api_key="fake", goal="general")

    assert len(leads) == 2, "Expected exactly 2 leads"
    for lead in leads:
        assert "lead_score" in lead, f"Missing lead_score on {lead['business_name']}"
        assert "lead_tier" in lead, f"Missing lead_tier on {lead['business_name']}"
        assert isinstance(lead["lead_score"], (int, float))
    # Different names → dedup must keep both
    names = {lead["business_name"] for lead in leads}
    assert len(names) == 2, f"Dedup incorrectly merged distinct leads: {names}"


# ── Test 2: Fuzzy deduplication ──────────────────────────────────────


@pytest.mark.asyncio
async def test_deduplication_merges_similar_names(base_config):
    """Two leads whose names differ only by an accent → merged to 1."""
    places_search = {
        "status": "OK",
        "results": [
            _make_place(
                "p1", "Barbería El Corte", "Av. Principal 100, Santiago", 4.8, 20, ["barber_shop"]
            ),
            _make_place(
                "p2",
                "Barberia El Corte",  # accent dropped
                "Av. Principal 102, Santiago",
                3.5,
                3,
                ["barber_shop"],
            ),
        ],
        "next_page_token": None,
    }

    mock_session = _build_mock_session(_make_get_side_effect(places_search))

    with (
        patch("aiohttp.ClientSession", return_value=mock_session),
        patch("pipeline.tqdm", MagicMock()),
    ):
        leads = await run_pipeline(base_config, api_key="fake", goal="general")

    assert len(leads) == 1, f"Fuzzy dedup failed — expected 1 lead, got {len(leads)}"
    # Higher-scored variant should survive
    assert leads[0]["business_name"] == "Barbería El Corte"
    assert leads[0]["google_rating"] == 4.8


# ── Test 3: Limit enforcement ────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_respects_limit(base_config):
    """API returns many leads but limit=2 caps the total.

    Pipeline now calls search_with_grid(), which geocodes first then
    uses Nearby Search per grid cell.  We use a tiny viewport so only
    1 grid cell is generated per call, yielding 1 lead per combo.
    A counter gives each lead a unique name so dedup doesn't merge them.
    """
    lead_names = ["Barbería Alpha", "Cafetería Beta"]
    lead_counter = [0]

    def get_side_effect(*args, **kwargs):
        url = args[0]

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.url = url
        mock_resp.history = []
        mock_resp.headers = {}

        if "geocode" in url:
            # Tiny viewport → only 1 grid cell per search_with_grid call
            mock_resp.json = AsyncMock(
                return_value={
                    "status": "OK",
                    "results": [
                        {
                            "geometry": {
                                "viewport": {
                                    "southwest": {"lat": -33.45, "lng": -70.65},
                                    "northeast": {"lat": -33.44, "lng": -70.64},
                                }
                            }
                        }
                    ],
                }
            )
        elif "nearbysearch" in url:
            idx = lead_counter[0]
            lead_counter[0] += 1
            name = lead_names[idx % len(lead_names)]
            mock_resp.json = AsyncMock(
                return_value={
                    "status": "OK",
                    "results": [
                        _make_place(
                            f"p{idx}",
                            name,
                            "Calle Test, Santiago",
                            4.5,
                            10,
                            ["barber_shop"],
                        ),
                    ],
                    "next_page_token": None,
                }
            )
        elif "details" in url:
            mock_resp.json = AsyncMock(return_value={"result": {}})
        elif "hunter.io" in url:
            mock_resp.json = AsyncMock(return_value={"data": {"emails": []}})
        else:
            mock_resp.text = AsyncMock(return_value="<html></html>")
            mock_resp.json = AsyncMock(return_value={})

        return _mock_context_manager(mock_resp)

    mock_session = _build_mock_session(get_side_effect)

    with (
        patch("aiohttp.ClientSession", return_value=mock_session),
        patch("pipeline.tqdm", MagicMock()),
    ):
        leads = await run_pipeline(base_config, api_key="fake", goal="general", limit=2)

    assert len(leads) == 2, f"Limit not enforced: expected 2, got {len(leads)}"


# ── Test 4: SEO audit flag ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_seo_audit_populates_audit_data(base_config):
    """do_seo=True + lead with website → audit_data present."""
    places_search = {
        "status": "OK",
        "results": [
            _make_place(
                "p1", "Barbería SEO Test", "Av. SEO 123, Santiago", 4.5, 15, ["barber_shop"]
            ),
        ],
        "next_page_token": None,
    }
    places_detail = {
        "result": {
            "website": "https://seo-test.cl",
            "formatted_phone_number": "+56987654321",
            "international_phone_number": "+56987654321",
            "url": "https://maps.google.com/seo",
        }
    }

    # Mock the WebsiteAnalyzer to return a canned audit result.
    # This keeps the test focused on pipeline orchestration, not
    # the analyzer's complex HTTP/HTML parsing logic.
    mock_analyzer = AsyncMock()
    mock_analyzer.analyze = AsyncMock(
        return_value={
            "seo": {"has_h1": True, "has_meta_description": False},
            "performance": {"load_time_ms": 1200},
        }
    )

    mock_session = _build_mock_session(_make_get_side_effect(places_search, places_detail))

    with (
        patch("aiohttp.ClientSession", return_value=mock_session),
        patch("pipeline.tqdm", MagicMock()),
        patch("pipeline.WebsiteAnalyzer", return_value=mock_analyzer),
    ):
        leads = await run_pipeline(base_config, api_key="fake", goal="seo", do_seo=True)

    assert len(leads) == 1
    assert "audit_data" in leads[0], "audit_data missing — SEO audit not run"
    audit = leads[0]["audit_data"]
    assert audit["seo"]["has_meta_description"] is False
    assert audit["performance"]["load_time_ms"] == 1200


# ── Test 5: Empty results ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_results_handled_gracefully(base_config):
    """Places API returns ZERO_RESULTS → empty list, no crash."""
    places_search = {
        "status": "ZERO_RESULTS",
        "results": [],
        "next_page_token": None,
    }

    mock_session = _build_mock_session(_make_get_side_effect(places_search))

    with (
        patch("aiohttp.ClientSession", return_value=mock_session),
        patch("pipeline.tqdm", MagicMock()),
    ):
        leads = await run_pipeline(base_config, api_key="fake", goal="general")

    assert leads == [], f"Expected empty list for ZERO_RESULTS, got {leads}"


# ── Test 6: No API key still works (extractor gets results dict back) ─


@pytest.mark.asyncio
async def test_pipeline_handles_api_errors(base_config):
    """Places API returns REQUEST_DENIED → pipeline returns empty, no crash."""
    places_search = {
        "status": "REQUEST_DENIED",
        "error_message": "Invalid API key",
        "results": [],
    }

    mock_session = _build_mock_session(_make_get_side_effect(places_search))

    with (
        patch("aiohttp.ClientSession", return_value=mock_session),
        patch("pipeline.tqdm", MagicMock()),
    ):
        leads = await run_pipeline(base_config, api_key="bad_key", goal="general")

    assert leads == [], f"Expected empty list on API error, got {len(leads)} leads"
