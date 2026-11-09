"""Tests for how a single lead is enriched."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pipeline import _enrich_lead


def _lead(**overrides) -> dict:
    return {
        "business_name": "Cafe Central",
        "city": "Santiago",
        "phone": "+56912345678",
        "website": "",
        **overrides,
    }


@pytest.mark.asyncio
async def test_lead_without_website_gets_no_instagram_handle() -> None:
    updates = await _enrich_lead(_lead(), MagicMock(), hunter_key="")

    assert "instagram_handle" not in updates


@pytest.mark.asyncio
async def test_handle_found_on_the_business_website_is_kept() -> None:
    enricher = MagicMock()
    enricher.scan_website = AsyncMock(return_value={"instagram": "cafecentral"})

    updates = await _enrich_lead(
        _lead(website="https://cafecentral.example"),
        enricher,
        hunter_key="",
    )

    assert updates["instagram_handle"] == "@cafecentral"


@pytest.mark.asyncio
async def test_whatsapp_fallback_from_phone_still_runs() -> None:
    updates = await _enrich_lead(_lead(), MagicMock(), hunter_key="")

    assert updates["whatsapp_link"] == "https://wa.me/56912345678"
    assert updates["whatsapp_phone"] == "+56912345678"
