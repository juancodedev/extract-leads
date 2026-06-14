"""
CLI entry point for the Lead Extractor pipeline.
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

import yaml
from dotenv import load_dotenv

# Load environment variables at module level (same as original pipeline.py)
load_dotenv(".env.local")
load_dotenv(".env")

from config_loader import load_config, get_default_industries, get_default_locations
from pipeline import run_pipeline
from exporters import export_csv, load_leads_from_csv
from reporters import print_summary, export_html
from analyzer import generate_audit_report

logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(
        description="Lead Extractor - Automated lead finding via Google Places API"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    parser.add_argument(
        "--output",
        default="leads_output/leads.csv",
        help="Output CSV path (default: leads_output/leads.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max leads to extract (0 = unlimited)",
    )
    parser.add_argument(
        "--google-key",
        help="Google Places API key (overrides GOOGLE_PLACES_API_KEY env var)",
    )
    parser.add_argument(
        "--hunter-key",
        help="Hunter.io API key (overrides HUNTER_API_KEY env var)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode (asks questions)",
    )
    parser.add_argument(
        "--html",
        help="Generate HTML report from existing CSV (usage: --html report.html)",
    )
    parser.add_argument(
        "--from-csv",
        help="Path to existing CSV to use with --html",
    )
    parser.add_argument(
        "--audit",
        help="Run website audit on leads CSV and output HTML report",
    )
    parser.add_argument(
        "--goal",
        choices=["web", "seo", "ads", "general"],
        default="general",
        help="Opportunity goal for scoring (default: general)",
    )
    parser.add_argument(
        "--seo",
        action="store_true",
        help="Enable deep SEO audits for top prospects",
    )
    parser.add_argument(
        "--ads",
        action="store_true",
        help="Mark top prospects for Meta Ads audit",
    )
    parser.add_argument(
        "--ig-web",
        action="store_true",
        help="Mark top prospects for Instagram-to-Web prototype",
    )
    args = parser.parse_args()

    # Audit mode
    if args.audit:
        if not args.from_csv:
            logger.error("--audit requiere --from-csv <archivo.csv>")
            sys.exit(1)
        leads = load_leads_from_csv(args.from_csv)
        await generate_audit_report(leads, args.audit)
        return

    # HTML report mode from existing CSV
    if args.from_csv and args.html:
        leads = load_leads_from_csv(args.from_csv)
        export_html(leads, args.html)
        print_summary(leads)
        return

    # Interactive mode
    if args.interactive:
        run_interactive()
        return

    # Load configuration
    config = load_config(args.config)

    # API keys
    api_key = args.google_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        print("\n🔑 No se detectó GOOGLE_PLACES_API_KEY en .env o variables de entorno.")
        api_key = input("Introduce tu API Key de Google Places (o presiona Enter para cancelar): ").strip()
        if not api_key:
            logger.error("Se requiere la API Key de Google Places para continuar.")
            sys.exit(1)

    hunter_key = args.hunter_key or os.environ.get("HUNTER_API_KEY", "")
    if hunter_key:
        logger.info("Hunter.io email enrichment enabled")
    else:
        logger.info("No Hunter.io key set — skipping email enrichment")

    # Show config summary
    search_cfg = config.get("search", {})
    industries = [i["name"] for i in search_cfg.get("industries", [])]
    locations = [l["city"] for l in search_cfg.get("locations", [])]
    target = search_cfg.get("target_size", "micro")

    print()
    print("=" * 55)
    print("  LEAD EXTRACTOR PIPELINE")
    print("=" * 55)
    print(f"  Industries : {', '.join(industries)}")
    print(f"  Locations  : {len(locations)} cities across Chile")
    print(f"  Target     : {target} businesses (1-10 employees)")
    print(f"  Limit      : {'unlimited' if not args.limit else args.limit}")
    print()

    # Run
    leads = await run_pipeline(
        config, api_key, hunter_key, args.limit,
        goal=args.goal, do_seo=args.seo, do_ads=args.ads, do_ig_web=args.ig_web
    )

    if not leads:
        logger.warning("No leads found. Try expanding keywords or locations.")
        sys.exit(0)

    export_csv(leads, args.output)
    print_summary(leads)

    return leads


def run_interactive():
    """Interactive mode: asks questions, builds config, and runs the prospecting engine."""
    print("\n" + "="*55)
    print(" 🚀 PROSPECTING ENGINE & BUSINESS AUDITOR")
    print("="*55)
    print("\n--- CONFIGURACIÓN DE BÚSQUEDA ---")

    # API key
    api_key = input("🔑 Google Places API key: ").strip()
    if not api_key:
        api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        logger.error("Se necesita una API key de Google Places")
        sys.exit(1)

    hunter_key = input("🔑 Hunter.io API key (opcional): ").strip()
    if not hunter_key:
        hunter_key = os.environ.get("HUNTER_API_KEY", "")

    # Load defaults (never reads config.yaml — avoids circular dep on first run)
    AVAILABLE_INDUSTRIES = get_default_industries()
    ALL_CITIES = get_default_locations()

    # Industries
    print("\n📋 Industrias disponibles:")
    for key, ind in sorted(AVAILABLE_INDUSTRIES.items(), key=lambda x: int(x[0])):
        print(f"  [{key}] {ind['name']}")
    print(f"  [{len(AVAILABLE_INDUSTRIES)+1}] Otra industria (especificar)")

    selected = input("\n¿Qué industrias? (ej: 1,2,3 o 'todas'): ").strip()

    chosen_industries = []
    if selected.lower() in ("todas", "all", "*"):
        chosen_industries = list(AVAILABLE_INDUSTRIES.values())
    elif selected == str(len(AVAILABLE_INDUSTRIES) + 1):
        custom_name = input("  Nombre de la industria: ").strip()
        custom_kws = input("  Palabras clave (separadas por coma): ").strip().split(",")
        chosen_industries.append({
            "name": custom_name,
            "keywords": [k.strip() for k in custom_kws],
            "bonus_score": 5
        })
    else:
        for s in selected.split(","):
            s = s.strip()
            if s in AVAILABLE_INDUSTRIES:
                chosen_industries.append(AVAILABLE_INDUSTRIES[s])

    if not chosen_industries:
        logger.error("No seleccionaste ninguna industria válida")
        sys.exit(1)

    # Cities
    print("\n📍 Regiones disponibles:")
    regions = sorted(set(c["region"] for c in ALL_CITIES))
    for i, r in enumerate(regions, 1):
        print(f"  [{i}] {r}")
    print(f"  [{len(regions)+1}] Todas las regiones")
    region_choice = input("\n¿Qué región(es)? (ej: 1,2 o 'todas'): ").strip()

    if region_choice.lower() in ("todas", "all", "*") or region_choice == str(len(regions) + 1):
        chosen_cities = ALL_CITIES
    else:
        chosen_regions = []
        for s in region_choice.split(","):
            s = s.strip()
            try:
                idx = int(s) - 1
                if 0 <= idx < len(regions):
                    chosen_regions.append(regions[idx])
            except ValueError:
                pass
        chosen_cities = [c for c in ALL_CITIES if c["region"] in chosen_regions]

    if not chosen_cities:
        chosen_cities = ALL_CITIES

    # Goal
    print("\n🎯 ¿Cuál es tu objetivo? (Esto ajusta la puntuación):")
    print("  [1] Vender Diseño Web (oportunidad si NO tienen web)")
    print("  [2] Vender SEO (oportunidad si tienen web pero mal SEO)")
    print("  [3] Vender Ads (oportunidad si tienen web y necesitan tráfico)")
    print("  [4] General (calidad de presencia digital)")
    goal_choice = input("\nElige una opción (1-4, default: 4): ").strip()
    goal_map = {"1": "web", "2": "seo", "3": "ads", "4": "general"}
    goal = goal_map.get(goal_choice, "general")

    # --- ADVANCED AUDIT OPTIONS ---
    print("\n🛠  AUDITORÍAS ADICIONALES (Para los mejores prospectos):")
    do_seo = input("  ¿Realizar auditoría SEO técnica profunda? (s/n, default: s): ").strip().lower() != "n"
    do_ads = input("  ¿Analizar anuncios en Meta Ads Library? (s/n, default: n): ").strip().lower() == "s"
    do_ig_web = input("  ¿Generar prototipo Instagram → Web? (s/n, default: n): ").strip().lower() == "s"

    # Limit (fixed: removed duplicate try/except bug from original)
    limit_str = input("\n🔢 ¿Cuántos leads quieres extraer? (default: 100): ").strip()
    try:
        limit = int(limit_str) if limit_str else 100
    except ValueError:
        limit = 100

    print(f"\n  Industrias: {[i['name'] for i in chosen_industries]}")
    print(f"  Ciudades:   {len(chosen_cities)}")
    print(f"  Límite:     {limit} leads")
    print()

    # Build config
    config = {
        "business": {"name": "Mi Negocio", "product_type": "automatización", "description": ""},
        "search": {
            "industries": chosen_industries,
            "locations": chosen_cities,
            "target_size": "micro",
        },
        "extraction": {
            "max_pages": 3,
            "page_token_delay": 2,
            "request_timeout": 15,
        },
        "enrichment": {
            "hunter_timeout": 10,
            "website_scan_timeout": 10,
        },
        "scoring": {
            "base_score": 50,
            "max_score": 100,
            "dup_threshold": 85,
            "weights": {
                "website": 15,
                "active_social": 20,
                "whatsapp": 10,
                "pain_points": 15,
                "multiple_channels": 10,
                "owner_info": 5,
                "premium_location": 10,
                "employees_5plus": 8,
                "years_2plus": 7,
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
            },
            "tiers": {"hot": [80, 100], "warm": [60, 79], "cool": [40, 59], "cold": [0, 39]},
        },
        "output": {"format": "csv", "fields": []},
    }

    # Run
    leads = asyncio.run(run_pipeline(
        config, api_key, hunter_key, limit,
        goal=goal, do_seo=do_seo, do_ads=do_ads, do_ig_web=do_ig_web
    ))

    if not leads:
        logger.warning("No se encontraron leads. Intenta con más industrias o ciudades.")
        sys.exit(0)

    output = f"leads_output/leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    export_csv(leads, output)
    print_summary(leads)

    # Write config.yaml so subsequent --config runs work
    config_path = "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    logger.info("Configuración guardada en %s", config_path)

    # Offer HTML
    html_choice = input("\n¿Generar reporte HTML? (s/n, default: s): ").strip().lower()
    if html_choice != "n":
        html_output = output.replace(".csv", ".html")
        export_html(leads, html_output)
        print(f"  HTML: {html_output}")

    # Offer audit
    audit_choice = input("\n¿Auditar websites? (s/n, default: s): ").strip().lower()
    if audit_choice != "n":
        audit_output = output.replace(".csv", "_audit.html")
        asyncio.run(generate_audit_report(leads, audit_output))

    print("\n✅ Listo!")
