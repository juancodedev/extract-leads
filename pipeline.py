#!/usr/bin/env python3
"""
Lead Extraction Pipeline - CLI tool.

Finds, enriches, scores, and exports business leads automatically
using Google Places API and optional Hunter.io enrichment.

Usage:
    # Interactive mode (asks you questions)
    python pipeline.py --interactive

    # With config file
    python pipeline.py --config config.yaml --limit 100

    # Generate HTML report from existing CSV
    python pipeline.py --from-csv leads.csv --html report.html
"""
import argparse
import csv
import json
import logging
import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, List

import yaml

from extractor import PlacesExtractor
from enricher import Enricher
from lead_scorer import LeadScorer

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


AVAILABLE_INDUSTRIES = {
    "1": {
        "name": "Barbería y Peluquería",
        "keywords": ["barbería", "barber", "barbershop", "peluquería", "salón de belleza", "corte de cabello", "barber shop", "barba", "barberia"],
        "bonus_score": 5,
    },
    "2": {
        "name": "Cafetería y Restaurante",
        "keywords": ["cafetería", "café", "coffee shop", "restaurante", "panadería", "pastelería"],
        "bonus_score": 5,
    },
    "3": {
        "name": "Servicios Profesionales",
        "keywords": ["contador", "consultor", "abogado", "asesor", "estudio contable", "consultoría"],
        "bonus_score": 5,
    },
    "4": {
        "name": "Salud y Belleza",
        "keywords": ["spa", "masajes", "centro de estética", "clínica estética", "depilación", "tratamientos faciales", "estética", "belleza", "wellness", "centro de belleza", "salón de uñas"],
        "bonus_score": 3,
    },
    "5": {
        "name": "Tiendas y Retail",
        "keywords": ["minimarket", "ferretería", "tienda", "almacén", "boutique", "almacen"],
        "bonus_score": 3,
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
}

ALL_CITIES = [
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


def load_config(path: str) -> Dict:
    """Load YAML configuration file."""
    if not os.path.exists(path):
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_pipeline(
    config: Dict,
    api_key: str,
    hunter_key: str = "",
    limit: int = 0,
) -> List[Dict]:
    """Execute the full extraction pipeline.

    For each industry keyword x location pair, searches Google Places,
    enriches results, and applies scoring.

    Returns:
        List of scored lead dicts.
    """
    extractor = PlacesExtractor(api_key)
    enricher = Enricher(hunter_key if hunter_key else None)
    scorer = LeadScorer(config)

    all_leads: List[Dict] = []
    seen_names: set = set()

    search_config = config.get("search", {})
    industries = search_config.get("industries", [])
    locations = search_config.get("locations", [])

    # Distribute limit across industries for balanced results
    per_industry_limit = 0
    if limit:
        per_industry_limit = limit // len(industries) if industries else limit

    total_combos = len(industries) * len(locations)
    done = 0

    for industry in industries:
        industry_leads = 0

        for keyword in industry.get("keywords", []):
            for loc in locations:
                if per_industry_limit and industry_leads >= per_industry_limit:
                    break
                if limit and len(all_leads) >= limit:
                    break
                done += 1

                logger.info(
                    "[%d/%d] Searching '%s' in %s, %s",
                    done, total_combos, keyword, loc["city"], loc["region"],
                )

                try:
                    results = extractor.search_businesses(
                        keyword, f"{loc['city']}, {loc['region']}"
                    )
                except Exception as e:
                    logger.error("Search failed: %s", e)
                    continue

                for place in results:
                    name = place.get("business_name", "")
                    if not name or name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    industry_name = LeadScorer.classify_industry(
                        place.get("types", []),
                        name,
                        config,
                    )

                    lead = {
                        "business_name": name,
                        "industry": industry_name,
                        "contact_person": "",
                        "phone": (
                            place.get("international_phone")
                            or place.get("phone", "")
                        ),
                        "email": "",
                        "address": place.get("address", ""),
                        "city": LeadScorer.extract_city(
                            place.get("address", ""), config
                        ),
                        "website": place.get("website", ""),
                        "facebook_url": "",
                        "instagram_handle": "",
                        "linkedin_url": "",
                        "google_rating": place.get("rating"),
                        "review_count": place.get("total_ratings", 0),
                        "google_type": ", ".join(place.get("types", [])),
                        "source": "Google Maps",
                        "date_found": datetime.now().strftime("%Y-%m-%d"),
                    }

                    # Email enrichment via Hunter.io
                    if lead["website"] and hunter_key:
                        domain = Enricher.extract_domain(lead["website"])
                        if domain:
                            email = enricher.find_email(domain)
                            if email:
                                lead["email"] = email

                    # Social media detection from website
                    if lead["website"]:
                        social = enricher.detect_social(
                            lead["website"], name
                        )
                        lead["facebook_url"] = social.get("facebook") or ""
                        lead["instagram_handle"] = social.get("instagram") or ""
                        lead["linkedin_url"] = social.get("linkedin") or ""

                    # Scoring
                    lead = scorer.score(lead)
                    all_leads.append(lead)
                    industry_leads += 1

                    if limit and len(all_leads) >= limit:
                        break

            if limit and len(all_leads) >= limit:
                break

        if per_industry_limit and industry_leads >= per_industry_limit:
            logger.info(
                "Reached %d leads for '%s', moving to next industry",
                industry_leads, industry.get("name"),
            )

    return all_leads


def export_csv(leads: List[Dict], output_path: str):
    """Write leads to CSV file."""
    fieldnames = [
        "business_name",
        "industry",
        "contact_person",
        "phone",
        "email",
        "address",
        "city",
        "website",
        "facebook_url",
        "instagram_handle",
        "linkedin_url",
        "google_rating",
        "review_count",
        "lead_score",
        "lead_tier",
        "scoring_notes",
        "source",
        "date_found",
    ]

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, restval="", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(leads)

    logger.info("Exported %d leads to %s", len(leads), output_path)


def print_summary(leads: List[Dict]):
    """Print a summary of results to stdout."""
    if not leads:
        print("\n No leads found.")
        return

    tiers: Dict[str, int] = {}
    industries: Dict[str, int] = {}

    for lead in leads:
        t = lead.get("lead_tier", "UNKNOWN")
        tiers[t] = tiers.get(t, 0) + 1
        ind = lead.get("industry", "Unknown")
        industries[ind] = industries.get(ind, 0) + 1

    print()
    print("=" * 55)
    print("  LEAD EXTRACTION SUMMARY")
    print("=" * 55)
    print(f"  Total leads extracted: {len(leads)}")
    print()

    tier_order = ["HOT", "WARM", "COOL", "COLD"]
    for tier in tier_order:
        count = tiers.get(tier, 0)
        if count:
            pct = count * 100 // len(leads)
            print(f"  {tier:8} : {count:4} ({pct:2}%)")

    print()
    print("  By industry:")
    for ind, count in sorted(industries.items(), key=lambda x: -x[1]):
        print(f"    {ind:35} : {count}")
    print("=" * 55)
    print()


def run_interactive():
    """Interactive mode: asks questions, builds config, runs extraction."""
    print()
    print("=" * 55)
    print("  LEAD EXTRACTOR — MODO INTERACTIVO")
    print("=" * 55)
    print()

    # API key
    api_key = input("🔑 Google Places API key: ").strip()
    if not api_key:
        api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not api_key:
        logger.error("Se necesita una API key de Google Places")
        sys.exit(1)

    hunter_key = input("🔑 Hunter.io API key (opcional, para emails): ").strip()
    if not hunter_key:
        hunter_key = os.environ.get("HUNTER_API_KEY", "")

    # Industries
    print("\n📋 Industrias disponibles:")
    for key, ind in AVAILABLE_INDUSTRIES.items():
        print(f"  [{key}] {ind['name']}")
    selected = input("\n¿Qué industrias? (ej: 1,2,3 o 'todas'): ").strip()
    if selected.lower() in ("todas", "all", "*"):
        chosen_industries = list(AVAILABLE_INDUSTRIES.values())
    else:
        chosen_industries = []
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

    # Limit
    limit_str = input("\n🔢 ¿Cuántos leads quieres? (default: 100): ").strip()
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
        "scoring": {
            "base_score": 50,
            "max_score": 100,
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
            "tiers": {"hot": [80, 100], "warm": [60, 79], "cool": [40, 59], "cold": [0, 39]},
        },
        "output": {"format": "csv", "fields": []},
        "api_keys": {"google_places": api_key, "hunter": hunter_key},
    }

    # Run
    leads = run_pipeline(config, api_key, hunter_key, limit)

    if not leads:
        logger.warning("No se encontraron leads. Intenta con más industrias o ciudades.")
        sys.exit(0)

    output = f"leads_output/leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    export_csv(leads, output)
    print_summary(leads)

    # Offer HTML
    html_choice = input("\n¿Generar reporte HTML? (s/n, default: s): ").strip().lower()
    if html_choice != "n":
        html_output = output.replace(".csv", ".html")
        export_html(leads, html_output)
        print(f"  HTML: {html_output}")

    print("\n✅ Listo!")



def export_html(leads: List[Dict], output_path: str):
    """Generate a clean HTML report from leads data."""
    tiers_count = {}
    industries_count = {}
    total = len(leads)
    phones = sum(1 for l in leads if l.get("phone"))
    websites = sum(1 for l in leads if l.get("website"))
    avg_rating = 0.0
    ratings_n = 0
    for l in leads:
        t = l.get("lead_tier", "UNKNOWN")
        tiers_count[t] = tiers_count.get(t, 0) + 1
        ind = l.get("industry", "Unknown")
        industries_count[ind] = industries_count.get(ind, 0) + 1
        r = l.get("google_rating")
        if r:
            try:
                avg_rating += float(r)
                ratings_n += 1
            except (ValueError, TypeError):
                pass
    avg_rating = avg_rating / ratings_n if ratings_n else 0

    tier_colors = {"HOT": "#ef4444", "WARM": "#f59e0b", "COOL": "#3b82f6", "COLD": "#6b7280"}
    tier_bg = {"HOT": "rgba(239,68,68,0.1)", "WARM": "rgba(245,158,11,0.1)", "COOL": "rgba(59,130,246,0.1)", "COLD": "rgba(107,114,128,0.1)"}

    rows_html = ""
    for i, l in enumerate(leads, 1):
        tier = l.get("lead_tier", "COLD")
        color = tier_colors.get(tier, "#6b7280")
        bg = tier_bg.get(tier, "transparent")
        score = l.get("lead_score", 0)
        rating = l.get("google_rating", "")
        reviews = l.get("review_count", "")
        phone = l.get("phone", "")
        website = l.get("website", "")
        ig = l.get("instagram_handle", "")
        fb = l.get("facebook_url", "")

        contact_icons = ""
        if phone:
            contact_icons += f'<span class="contact-badge phone" title="{phone}">📞</span>'
        if website:
            contact_icons += f'<span class="contact-badge web" title="{website}">🌐</span>'
        if ig:
            contact_icons += f'<span class="contact-badge ig" title="{ig}">📸</span>'
        if fb:
            contact_icons += f'<span class="contact-badge fb" title="{fb}">👍</span>'

        rows_html += f"""\
<tr>
  <td class="num">{i}</td>
  <td><strong>{l.get("business_name", "")}</strong></td>
  <td>{l.get("industry", "")}</td>
  <td>{l.get("city", "")}</td>
  <td class="contacts">{contact_icons}</td>
  <td class="num">{rating}</td>
  <td class="num">{reviews}</td>
  <td><span class="tier" style="background:{bg};color:{color};border:1px solid {color}">{tier}</span></td>
  <td class="num"><strong>{score}</strong></td>
</tr>"""

    tiers_html = ""
    for t in ["HOT", "WARM", "COOL", "COLD"]:
        c = tiers_count.get(t, 0)
        if c:
            pct = c * 100 // total
            tiers_html += f"""\
    <div class="stat">
      <div class="stat-value" style="color:{tier_colors[t]}">{c}</div>
      <div class="stat-label">{t} <span style="color:#94a3b8">({pct}%)</span></div>
    </div>"""

    ind_html = ""
    for ind_name, count in sorted(industries_count.items(), key=lambda x: -x[1]):
        pct = count * 100 // total
        ind_html += f"""\
    <div class="ind-bar">
      <div class="ind-name">{ind_name}</div>
      <div class="ind-track"><div class="ind-fill" style="width:{pct}%"></div></div>
      <div class="ind-count">{count}</div>
    </div>"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""\
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lead Report — {total} leads</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#f8fafc; color:#1e293b; }}
.container {{ max-width:1280px; margin:0 auto; padding:24px 20px; }}
.header {{ margin-bottom:32px; }}
.header h1 {{ font-size:28px; font-weight:700; }}
.header p {{ color:#64748b; margin-top:4px; font-size:14px; }}
.stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:32px; }}
.stat {{ background:#fff; border-radius:12px; padding:16px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
.stat-value {{ font-size:32px; font-weight:700; }}
.stat-label {{ font-size:13px; color:#64748b; margin-top:2px; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:32px; }}
@media (max-width:768px) {{ .cards {{ grid-template-columns:1fr; }} }}
.card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
.card h3 {{ font-size:15px; font-weight:600; margin-bottom:12px; color:#475569; }}
.ind-bar {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
.ind-name {{ font-size:13px; width:180px; flex-shrink:0; }}
.ind-track {{ flex:1; height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden; }}
.ind-fill {{ height:100%; background:#3b82f6; border-radius:4px; transition:width 0.4s; }}
.ind-count {{ font-size:13px; color:#64748b; width:30px; text-align:right; }}
.table-wrap {{ background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ background:#f8fafc; text-align:left; padding:12px 8px; font-weight:600; color:#475569; border-bottom:2px solid #e2e8f0; white-space:nowrap; }}
td {{ padding:10px 8px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }}
tr:hover {{ background:#f8fafc; }}
.num {{ text-align:center; }}
.contacts {{ white-space:nowrap; }}
.contact-badge {{ cursor:default; font-size:14px; margin-right:2px; }}
.tier {{ display:inline-block; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; }}
.footer {{ text-align:center; padding:24px; color:#94a3b8; font-size:12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 Lead Report</h1>
    <p>{total} leads extraídos • {now} • {phones} con teléfono • {websites} con web • ⭐ {avg_rating:.1f} promedio</p>
  </div>

  <div class="stats-grid">
    <div class="stat">
      <div class="stat-value">{total}</div>
      <div class="stat-label">Total leads</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#22c55e">{phones}</div>
      <div class="stat-label">Con teléfono</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#3b82f6">{websites}</div>
      <div class="stat-label">Con website</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#f59e0b">{avg_rating:.1f}</div>
      <div class="stat-label">Rating promedio</div>
    </div>
{tiers_html}
  </div>

  <div class="cards">
    <div class="card">
      <h3>Por industria</h3>
{ind_html}
    </div>
    <div class="card">
      <h3>Por lead tier</h3>
      <div class="stats-grid" style="grid-template-columns:1fr 1fr; margin-bottom:0;">
{tiers_html}
      </div>
    </div>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th class="num">#</th>
          <th>Negocio</th>
          <th>Industria</th>
          <th>Ciudad</th>
          <th>Contacto</th>
          <th class="num">⭐</th>
          <th class="num">Reviews</th>
          <th>Tier</th>
          <th class="num">Score</th>
        </tr>
      </thead>
      <tbody>
{rows_html}
      </tbody>
    </table>
  </div>

  <div class="footer">Lead Extractor • {now}</div>
</div>
</body>
</html>"""

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Reporte HTML generado: %s", output_path)


def load_leads_from_csv(path: str) -> List[Dict]:
    """Load leads from a previously exported CSV."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
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
    args = parser.parse_args()

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
        logger.error(
            "No Google Places API key found.\n"
            "  Set GOOGLE_PLACES_API_KEY environment variable or\n"
            "  pass --google-key <key>"
        )
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
    leads = run_pipeline(config, api_key, hunter_key, args.limit)

    if not leads:
        logger.warning("No leads found. Try expanding keywords or locations.")
        sys.exit(0)

    export_csv(leads, args.output)
    print_summary(leads)

    return leads


if __name__ == "__main__":
    main()
