"""
Configuration loading and default industry/location data.
"""

import copy
import logging
import os
import sys
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "extraction": {
        "max_pages": 3,
        "page_token_delay": 3,
        "request_timeout": 15,
        "max_retries": 3,
        "retry_backoff": 1.5,
    },
    "enrichment": {
        "hunter_timeout": 10,
        "website_scan_timeout": 10,
        "max_retries": 3,
        "retry_backoff": 1.5,
    },
    "scoring": {
        "dup_threshold": 85,
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
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins."""
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


def _load_yaml(path: str) -> dict:
    """Load YAML file and return raw dict."""
    if not os.path.exists(path):
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


def _merge_with_defaults(cfg: dict) -> dict:
    """Fill missing config keys with defaults."""
    return _deep_merge(DEFAULT_CONFIG, cfg)


def load_config(path: str) -> dict[str, Any]:
    """Load YAML configuration file with defaults for missing keys."""
    raw = _load_yaml(path)
    return _merge_with_defaults(raw)


_FALLBACK_INDUSTRIES: dict[str, dict[str, Any]] = {
    "1": {
        "name": "Barbería y Peluquería",
        "keywords": [
            "barbería",
            "barber",
            "barbershop",
            "peluquería",
            "salón de belleza",
            "corte de cabello",
            "barber shop",
            "barba",
            "barberia",
        ],
        "bonus_score": 5,
    },
    "2": {
        "name": "Cafetería y Restaurante",
        "keywords": ["cafetería", "café", "coffee shop", "restaurante", "panadería", "pastelería"],
        "bonus_score": 5,
    },
    "3": {
        "name": "Servicios Profesionales",
        "keywords": [
            "contador",
            "consultor",
            "abogado",
            "asesor",
            "estudio contable",
            "consultoría",
        ],
        "bonus_score": 5,
    },
    "4": {
        "name": "Salud y Belleza",
        "keywords": [
            "spa",
            "masajes",
            "centro de estética",
            "clínica estética",
            "depilación",
            "tratamientos faciales",
            "estética",
            "belleza",
            "wellness",
            "centro de belleza",
            "salón de uñas",
        ],
        "bonus_score": 3,
    },
    "5": {
        "name": "Tiendas de Barrio y Minimarkets",
        "keywords": [
            "almacén", "minimarket", "tienda de barrio", "supermercado",
            "boutique", "ferretería", "librería", "almacen", "despensa",
        ],
        "bonus_score": 4,
    },
    "6": {
        "name": "Servicios de Limpieza",
        "keywords": ["limpieza", "aseo", "cleaning service", "mantención"],
        "bonus_score": 3,
    },
    "7": {
        "name": "Fitness y Bienestar",
        "keywords": ["gimnasio", "yoga", "pilates", "entrenador", "personal trainer", "crossfit"],
        "bonus_score": 3,
    },
    "8": {
        "name": "Educación y Tutorías",
        "keywords": ["tutoría", "clases", "profesor", "academia", "reforzamiento"],
        "bonus_score": 3,
    },
    "9": {
        "name": "Automotriz",
        "keywords": [
            "taller mecánico",
            "repuestos",
            "vulcanización",
            "car wash",
            "servicio técnico automotriz",
            "mecánica",
        ],
        "bonus_score": 4,
    },
    "10": {
        "name": "Mascotas",
        "keywords": [
            "veterinaria",
            "peluquería canina",
            "pet shop",
            "clínica veterinaria",
            "alimento mascotas",
        ],
        "bonus_score": 4,
    },
    "11": {
        "name": "Turismo y Hotelería",
        "keywords": ["hotel", "hostal", "turismo", "agencia de viajes", "cabañas", "alojamiento"],
        "bonus_score": 4,
    },
    "12": {
        "name": "Inmobiliaria y Construcción",
        "keywords": [
            "propiedades",
            "corredora",
            "construcción",
            "arquitecto",
            "remodelación",
            "gasfitería",
            "electricista",
        ],
        "bonus_score": 5,
    },
    "13": {
        "name": "Bares y Cervecerías",
        "keywords": [
            "bar", "pub", "cervecería", "bar de copas", "discoteca",
            "club nocturno", "barra", "cerveza artesanal",
        ],
        "bonus_score": 5,
    },
    "14": {
        "name": "Comida Rápida y Rotiserías",
        "keywords": [
            "rotisería", "delivery", "pizzería", "sushi",
            "comida rápida", "comida para llevar", "sandwichería",
            "comida china", "empanadas",
        ],
        "bonus_score": 5,
    },
    "15": {
        "name": "Heladerías y Postres",
        "keywords": [
            "heladería", "helado", "postres", "dulces",
            "gelato", "frozen yogurt", "paletas", "pastelería",
        ],
        "bonus_score": 4,
    },
}

_FALLBACK_LOCATIONS: list[dict[str, Any]] = [
    {"city": "Santiago", "region": "Metropolitana", "premium": True},
    {"city": "Las Condes", "region": "Metropolitana", "premium": True},
    {"city": "Providencia", "region": "Metropolitana", "premium": True},
    {"city": "Ñuñoa", "region": "Metropolitana", "premium": True},
    {"city": "Vitacura", "region": "Metropolitana", "premium": True},
    {"city": "La Florida", "region": "Metropolitana", "premium": False},
    {"city": "Maipú", "region": "Metropolitana", "premium": False},
    {"city": "Puente Alto", "region": "Metropolitana", "premium": False},
    {"city": "San Bernardo", "region": "Metropolitana", "premium": False},
    {"city": "Quilicura", "region": "Metropolitana", "premium": False},
    {"city": "Valparaíso", "region": "Valparaíso", "premium": False},
    {"city": "Viña del Mar", "region": "Valparaíso", "premium": True},
    {"city": "Concón", "region": "Valparaíso", "premium": False},
    {"city": "Concepción", "region": "Biobío", "premium": False},
    {"city": "Talcahuano", "region": "Biobío", "premium": False},
    {"city": "Chillán", "region": "Biobío", "premium": False},
    {"city": "Antofagasta", "region": "Antofagasta", "premium": False},
    {"city": "La Serena", "region": "Coquimbo", "premium": False},
    {"city": "Rancagua", "region": "O'Higgins", "premium": False},
    {"city": "Talca", "region": "Maule", "premium": False},
    {"city": "Temuco", "region": "Araucanía", "premium": False},
    {"city": "Puerto Montt", "region": "Los Lagos", "premium": False},
    {"city": "Iquique", "region": "Tarapacá", "premium": False},
    {"city": "Arica", "region": "Arica y Parinacota", "premium": False},
    {"city": "Copiapo", "region": "Atacama", "premium": False},
]


def get_default_industries() -> dict[str, dict[str, Any]]:
    """Return the full industry catalog for the interactive menu.

    Returns a dict with string keys '1'..'N' for menu ordering.
    This always returns the complete fallback list — the interactive
    menu shows ALL available options regardless of config.yaml contents.
    """
    return _FALLBACK_INDUSTRIES


def get_default_locations() -> list[dict[str, Any]]:
    """Return the full location catalog for the interactive menu.

    This always returns the complete fallback list — the interactive
    menu shows ALL available locations regardless of config.yaml contents.
    """
    return _FALLBACK_LOCATIONS
