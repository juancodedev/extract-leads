"""
Shared test fixtures for lead extractor tests.

Provides a minimal valid config dict matching what config_loader.DEFAULT_CONFIG
would produce after merging, so tests don't need a real config.yaml file.
"""

import pytest


@pytest.fixture
def base_config() -> dict:
    """Minimal config with all keys that LeadScorer expects."""
    return {
        "search": {
            "industries": [
                {
                    "name": "Barbería",
                    "keywords": ["barbería", "barber", "peluquería"],
                    "bonus_score": 5,
                },
                {
                    "name": "Cafetería",
                    "keywords": ["cafetería", "café", "restaurante"],
                    "bonus_score": 5,
                },
            ],
            "locations": [
                {"city": "Santiago", "region": "Metropolitana", "premium": True},
                {"city": "Maipú", "region": "Metropolitana", "premium": False},
            ],
        },
        "scoring": {
            "base_score": 50,
            "max_score": 100,
            "dup_threshold": 85,
            "weights": {
                "website": 15,
                "active_social": 20,
                "whatsapp": 10,
                "multiple_channels": 10,
                "premium_location": 10,
                "owner_info": 5,
                "pain_points": 15,
            },
            "thresholds": {
                "slow_ms": 3000,
                "warn_ms": 1500,
            },
            "goal_bonuses": {
                "web": {"no_site_bonus": 40, "has_site_penalty": -10},
                "seo": {"no_social_bonus": 20, "poor_tech_bonus": 30, "no_site_penalty": -20},
                "ads": {"has_site_bonus": 20, "low_rating_bonus": 15, "low_rating_threshold": 4.2},
                "general": {"high_rating_threshold": 4.5},
                "automatizacion": {
                    "no_site_bonus": 40,
                    "no_booking_bonus": 30,
                    "no_whatsapp_bonus": 20,
                    "has_site_no_booking_bonus": 15,
                },
                "reservas": {
                    "no_booking_bonus": 40,
                    "has_site_no_booking_bonus": 20,
                    "service_industry_bonus": 15,
                    "has_booking_penalty": -30,
                },
                "menus": {
                    "food_industry_bonus": 35,
                    "non_food_penalty": -10,
                    "no_prices_bonus": 30,
                    "no_gallery_bonus": 20,
                    "mature_site_penalty": -20,
                },
                "inventarios": {
                    "retail_industry_bonus": 30,
                    "has_site_bonus": 20,
                    "basic_cms_bonus": 15,
                    "has_booking_penalty": -10,
                },
                "pos": {
                    "phone_no_whatsapp_bonus": 30,
                    "no_site_bonus": 25,
                    "site_no_form_bonus": 20,
                    "digital_mature_penalty": -15,
                },
            },
            "tiers": {
                "hot": [80, 100],
                "warm": [60, 79],
                "cool": [40, 59],
                "cold": [0, 39],
            },
        },
    }


def make_lead(**overrides) -> dict:
    """Helper to build a lead dict with sensible defaults for testing."""
    lead = {
        "business_name": "Test Business",
        "industry": "Barbería",
        "phone": "+56912345678",
        "email": "",
        "website": "",
        "address": "Av. Test 123, Santiago",
        "city": "Santiago",
        "whatsapp_link": "",
        "facebook_url": "",
        "instagram_handle": "",
        "linkedin_url": "",
        "booking_links": "",
        "google_rating": 4.5,
        "review_count": 50,
        "google_type": "barber_shop",
        "contact_person": "",
        "audit_data": {},
        "needs_website": False,
        "needs_seo": False,
        "has_web_no_social": False,
    }
    lead.update(overrides)
    return lead
