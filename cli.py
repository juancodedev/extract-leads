"""
CLI entry point for the Lead Extractor pipeline.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import yaml
from dotenv import load_dotenv

# Load environment variables at module level (same as original pipeline.py)
load_dotenv(".env.local")
load_dotenv(".env")

from analyzer import generate_audit_report  # noqa: E402
from config_loader import get_default_industries, get_default_locations, load_config  # noqa: E402
from exporters import export_csv, load_leads_from_csv  # noqa: E402
from pipeline import run_pipeline  # noqa: E402
from reporters import export_html, print_summary  # noqa: E402

logger = logging.getLogger(__name__)

# ── CRM Helpers ──

CRM_API_URL = os.environ.get("CRM_API_URL", "https://crm.juancode.dev")


def _crm_authenticate() -> str | None:
    """Authenticate with CRM and return a JWT token."""
    email = os.environ.get("CRM_API_EMAIL", "")
    password = os.environ.get("CRM_API_PASSWORD", "")
    if not email or not password:
        logger.error("CRM_API_EMAIL y CRM_API_PASSWORD no están configuradas en .env.local")
        return None

    url = f"{CRM_API_URL}/api/auth/login"
    payload = json.dumps({"email": email, "password": password}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=15) as resp:
            resp.read().decode()  # drain body

            # CRM es Next.js + Supabase SSR — usa cookie de sesión, no Bearer token
            set_cookie = resp.getheader("set-cookie", "")
            for part in set_cookie.split(","):
                if "sb-" in part:
                    return part.split(";")[0]

            logger.error("No se encontró cookie de sesión Supabase")
            return None
    except HTTPError as e:
        body = e.read().decode()
        try:
            detail = json.loads(body)
            err_msg = detail.get("error", detail.get("detail", body))
        except json.JSONDecodeError:
            err_msg = body
        logger.error("Error CRM auth (%s): %s", e.code, err_msg)
        return None
    except URLError as e:
        logger.error("No se pudo conectar al CRM: %s", e.reason)
        return None


def _crm_send_lead(cookie: str, lead: dict) -> tuple[bool, str]:
    """Send a single lead to the CRM using Supabase session cookie. Returns (success, message)."""
    email = lead.get("email") or ""
    if not email or "@" not in email:
        import re
        name = lead.get("business_name") or lead.get("empresa") or "lead"
        email = re.sub(r"[^a-z0-9]", "", name.lower()) + "@sin-email.lead"

    payload = {
        "empresa": lead.get("business_name") or lead.get("empresa") or "",
        "email": email,
        "origen": "Lead Extractor - Google Maps",
        "nombre": lead.get("contact_person") or lead.get("nombre") or lead.get("business_name") or "",
        "telefono": lead.get("phone") or lead.get("telefono") or "",
        "notas": (
            f"Lead Score: {lead.get('lead_score', 'N/A')} | "
            f"Industria: {lead.get('industry', 'N/A')} | "
            f"Ciudad: {lead.get('city', 'N/A')}"
        ),
        "status": "Nuevo",
    }

    url = f"{CRM_API_URL}/api/leads"
    data = json.dumps(payload).encode()
    req = Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Cookie": cookie,
        },
    )

    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            return True, result.get("id", "ok")
    except HTTPError as e:
        body = e.read().decode()
        try:
            detail = json.loads(body)
            err_msg = detail.get("error", detail.get("detail", body))
        except json.JSONDecodeError:
            err_msg = body
        return False, f"HTTP {e.code}: {err_msg}"
    except URLError as e:
        return False, f"Error conexión: {e.reason}"


def crm_send_batch(csv_path: str):
    """Send all leads from a CSV to the CRM."""
    from exporters import load_leads_from_csv

    leads = load_leads_from_csv(csv_path)
    if not leads:
        logger.error("No se encontraron leads en %s", csv_path)
        sys.exit(1)

    logger.info("Autenticando con CRM...")
    cookie = _crm_authenticate()
    if not cookie:
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  Enviando {len(leads)} leads al CRM...")
    print(f"{'='*50}\n")

    success = 0
    errors = 0
    for i, lead in enumerate(leads, 1):
        name = lead.get("business_name", "Desconocido")
        ok, msg = _crm_send_lead(cookie, lead)
        if ok:
            success += 1
            print(f"  ✓ [{i}/{len(leads)}] {name} → CRM (id: {msg})")
        else:
            errors += 1
            print(f"  ✗ [{i}/{len(leads)}] {name} → {msg}")

    print(f"\n{'='*50}")
    print(f"  Resultado: {success} enviados, {errors} errores")
    print(f"{'='*50}")


def _print_dry_run(config, args):
    """Print a summary of what WOULD be searched without making API calls."""
    search_cfg = config.get("search", {})
    industries = search_cfg.get("industries", [])
    locations = search_cfg.get("locations", [])

    # Collect all keywords (with duplicates if shared across industries)
    all_keywords = []
    for ind in industries:
        all_keywords.extend(ind.get("keywords", []))
    total_keywords = len(all_keywords)

    # Count unique regions
    regions = {loc.get("region", "") for loc in locations}

    # Search combinations = sum over all industries of kws × locations
    total_combos = sum(len(ind.get("keywords", [])) * len(locations) for ind in industries)

    # Industry names
    industry_names = [ind.get("name", "Unknown") for ind in industries]

    # Active deep audit flags
    audits = []
    if args.seo:
        audits.append("SEO")
    if args.ads:
        audits.append("Meta Ads")
    if args.ig_web:
        audits.append("Instagram→Web")

    print()
    print("=== DRY RUN ===")
    print(f"Goal: {args.goal}")
    print(f"Industries: {len(industries)} ({', '.join(industry_names)})")
    print(f"Keywords: {', '.join(all_keywords)}")
    print(f"Locations: {len(locations)} cities in {len(regions)} regions")
    print(
        f"Search combinations: {total_keywords} keywords × "
        f"{len(locations)} cities = {total_combos}"
    )
    print(f"API calls estimated: ~{total_combos} search + details")
    limit_label = str(args.limit) if args.limit else "unlimited"
    print(f"Limit: {limit_label} leads")
    if audits:
        print(f"Deep audits: {', '.join(audits)}")
    print(f"Output: {args.output}")
    print("=== End dry run ===")
    print()


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
        help="Run website audit on leads CSV and output HTML report "
        "(usage: --audit leads.csv or --audit output.html --from-csv leads.csv)",
    )
    parser.add_argument("--version", action="version", version="lead-extractor 0.2.0")
    parser.add_argument(
        "--goal",
        choices=["web", "seo", "ads", "general", "automatizacion", "reservas", "menus", "inventarios", "pos"],
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be searched without making API calls",
    )
    parser.add_argument(
        "--crm-send",
        metavar="CSV",
        help="Send leads from a CSV file to the CRM in batch",
    )
    parser.add_argument(
        "--serve",
        nargs="?",
        const="auto",
        metavar="HTML",
        help="Serve a report HTML with CRM integration (uses latest if no path given)",
    )
    args = parser.parse_args()

    # CRM send mode (batch)
    if args.crm_send:
        crm_send_batch(args.crm_send)
        return

    # Serve mode
    if args.serve is not None:
        import subprocess
        serve_script = os.path.join(os.path.dirname(__file__), "serve_report.py")
        cmd = [sys.executable, serve_script]
        if args.serve != "auto":
            cmd.append(args.serve)
        logger.info("Iniciando servidor del reporte...")
        subprocess.run(cmd)
        return

    # Audit mode
    if args.audit:
        audit_arg = args.audit
        if audit_arg.endswith(".csv") and not args.from_csv:
            # --audit leads.csv → input=leads.csv, output=leads_audit.html
            leads = load_leads_from_csv(audit_arg)
            output = audit_arg.replace(".csv", "_audit.html")
        elif args.from_csv:
            # --audit output.html --from-csv leads.csv (backward compat)
            leads = load_leads_from_csv(args.from_csv)
            output = audit_arg
        else:
            logger.error("--audit requiere archivo CSV (ej: --audit leads.csv) o --from-csv")
            sys.exit(1)
        await generate_audit_report(leads, output)
        return

    # HTML report mode from existing CSV
    if args.from_csv and args.html:
        leads = load_leads_from_csv(args.from_csv)
        export_html(leads, args.html)
        print_summary(leads)
        return

    # Interactive mode
    if args.interactive:
        await run_interactive()
        return

    # Load configuration
    config = load_config(args.config)

    # Dry-run: preview what would happen without making any API calls
    if args.dry_run:
        _print_dry_run(config, args)
        return

    # API keys
    api_key = args.google_key or os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        print("\n🔑 No se detectó GOOGLE_PLACES_API_KEY en .env o variables de entorno.")
        api_key = input(
            "Introduce tu API Key de Google Places (o presiona Enter para cancelar): "
        ).strip()
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
    locations = [loc["city"] for loc in search_cfg.get("locations", [])]
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
        config,
        api_key,
        hunter_key,
        args.limit,
        goal=args.goal,
        do_seo=args.seo,
        do_ads=args.ads,
        do_ig_web=args.ig_web,
    )

    if not leads:
        logger.warning("No leads found. Try expanding keywords or locations.")
        sys.exit(0)

    export_csv(leads, args.output)
    print_summary(leads)

    return leads


async def run_interactive():
    """Interactive mode: asks questions, builds config, and runs the prospecting engine."""
    print("\n" + "=" * 55)
    print(" 🚀 PROSPECTING ENGINE & BUSINESS AUDITOR")
    print("=" * 55)
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
    available_industries = get_default_industries()
    all_cities = get_default_locations()

    # Industries
    print("\n📋 Industrias disponibles:")
    for key, ind in sorted(available_industries.items(), key=lambda x: int(x[0])):
        print(f"  [{key}] {ind['name']}")
    print(f"  [{len(available_industries)+1}] Otra industria (especificar)")

    selected = input("\n¿Qué industrias? (ej: 1,2,3 o 'todas'): ").strip()

    chosen_industries = []
    if selected.lower() in ("todas", "all", "*"):
        chosen_industries = list(available_industries.values())
    elif selected == str(len(available_industries) + 1):
        custom_name = input("  Nombre de la industria: ").strip()
        custom_kws = input("  Palabras clave (separadas por coma): ").strip().split(",")
        chosen_industries.append(
            {"name": custom_name, "keywords": [k.strip() for k in custom_kws], "bonus_score": 5}
        )
    else:
        for s in selected.split(","):
            s = s.strip()
            if s in available_industries:
                chosen_industries.append(available_industries[s])

    if not chosen_industries:
        logger.error("No seleccionaste ninguna industria válida")
        sys.exit(1)

    # Cities
    print("\n📍 Regiones disponibles:")
    regions = sorted({c["region"] for c in all_cities})
    for i, r in enumerate(regions, 1):
        print(f"  [{i}] {r}")
    print(f"  [{len(regions)+1}] Todas las regiones")
    region_choice = input("\n¿Qué región(es)? (ej: 1,2 o 'todas'): ").strip()

    if region_choice.lower() in ("todas", "all", "*") or region_choice == str(len(regions) + 1):
        chosen_cities = all_cities
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
        chosen_cities = [c for c in all_cities if c["region"] in chosen_regions]

    if not chosen_cities:
        chosen_cities = all_cities

    # Goal
    print("\n🎯 ¿Cuál es tu objetivo? (Esto ajusta la puntuación):")
    print("  [1] Vender Diseño Web (oportunidad si NO tienen web)")
    print("  [2] Vender SEO (oportunidad si tienen web pero mal SEO)")
    print("  [3] Vender Ads (oportunidad si tienen web y necesitan tráfico)")
    print("  [4] General (calidad de presencia digital)")
    print("  [5] Automatización (procesos, flujos de trabajo)")
    print("  [6] Sistema de Reservas (booking, turnos)")
    print("  [7] Menú Interactivo (QR, catálogo digital)")
    print("  [8] Sistema de Inventario (stock, control)")
    print("  [9] Sistema POS (punto de venta, checkout)")
    goal_choice = input("\nElige una opción (1-9, default: 4): ").strip()
    goal_map = {"1": "web", "2": "seo", "3": "ads", "4": "general",
                "5": "automatizacion", "6": "reservas", "7": "menus",
                "8": "inventarios", "9": "pos"}
    goal = goal_map.get(goal_choice, "general")

    # --- ADVANCED AUDIT OPTIONS ---
    print("\n🛠  AUDITORÍAS ADICIONALES (Para los mejores prospectos):")
    do_seo = (
        input("  ¿Realizar auditoría SEO técnica profunda? (s/n, default: s): ").strip().lower()
        != "n"
    )
    do_ads = (
        input("  ¿Analizar anuncios en Meta Ads Library? (s/n, default: n): ").strip().lower()
        == "s"
    )
    do_ig_web = (
        input("  ¿Generar prototipo Instagram → Web? (s/n, default: n): ").strip().lower() == "s"
    )

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
            "tiers": {"hot": [80, 100], "warm": [60, 79], "cool": [40, 59], "cold": [0, 39]},
        },
        "output": {"format": "csv", "fields": []},
    }

    # Run
    leads = await run_pipeline(
        config,
        api_key,
        hunter_key,
        limit,
        goal=goal,
        do_seo=do_seo,
        do_ads=do_ads,
        do_ig_web=do_ig_web,
    )

    if not leads:
        logger.warning("No se encontraron leads. Intenta con más industrias o ciudades.")
        sys.exit(0)

    output = f"leads_output/leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    export_csv(leads, output)
    print_summary(leads)

    # Ask before saving config
    config_path = "config.yaml"
    save_choice = input("\n¿Guardar esta configuración para futuras búsquedas? (s/n, default: s): ").strip().lower()
    if save_choice != "n":
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        logger.info("Configuración guardada en %s", config_path)
    else:
        logger.info("Configuración no guardada — solo en memoria.")

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
        await generate_audit_report(leads, audit_output)

    print("\n✅ Listo!")


def main_wrapper():
    """Entry point for console_scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    main_wrapper()
