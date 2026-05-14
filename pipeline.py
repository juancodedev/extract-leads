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
import html as html_lib
import json
import logging
import os
import re
import sys
import tempfile
from datetime import datetime
from typing import Dict, List

import yaml

from extractor import PlacesExtractor
from enricher import Enricher
from lead_scorer import LeadScorer
from analyzer import generate_audit_report

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
    goal: str = "general",
) -> List[Dict]:
    """Execute the full extraction pipeline.

    For each industry keyword x location pair, searches Google Places,
    enriches results, and applies scoring.

    Returns:
        List of scored lead dicts.
    """
    extractor = PlacesExtractor(api_key)
    enricher = Enricher(hunter_key if hunter_key else None)
    scorer = LeadScorer(config, goal=goal)

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
                        "whatsapp_link": "",
                        "booking_links": "",
                        "whatsapp_phone": "",
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

                    # Scan website for social, WhatsApp, booking links
                    if lead["website"]:
                        scan = enricher.scan_website(lead["website"], name)
                        lead["facebook_url"] = scan.get("facebook") or ""
                        ig = scan.get("instagram") or ""
                        lead["instagram_handle"] = f"@{ig}" if ig and not ig.startswith("@") else ig
                        lead["linkedin_url"] = scan.get("linkedin") or ""
                        lead["whatsapp_link"] = scan.get("whatsapp") or ""
                        booking = scan.get("booking_links", [])
                        lead["booking_links"] = " | ".join(booking) if booking else ""

                    # Generate WhatsApp link from phone as fallback
                    if not lead["whatsapp_link"] and lead["phone"]:
                        clean = re.sub(r"[^\d+]", "", lead["phone"])
                        if clean.startswith("+"):
                            lead["whatsapp_link"] = f"https://wa.me/{clean[1:]}"
                        else:
                            lead["whatsapp_link"] = f"https://wa.me/{clean}"
                    if lead["whatsapp_link"]:
                        lead["whatsapp_phone"] = lead["phone"]

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
        "whatsapp_link",
        "facebook_url",
        "instagram_handle",
        "linkedin_url",
        "booking_links",
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
    print("\n" + "="*55)
    print(" 🚀 LEAD EXTRACTOR & BUSINESS AUDITOR")
    print("="*55)
    print("\n¿Qué quieres hacer hoy?")
    print("  [1] Extracción de Leads (Google Places + Enrichment)")
    print("  [2] Auditoría SEO Completa")
    print("  [3] Auditoría de Meta Ads (Facebook/Instagram)")
    print("  [4] Auditoría de Negocio Digital (Holística)")
    print("  [5] Instagram → Web de Marca Personal")
    
    choice = input("\nElige una opción (1-5, default: 1): ").strip()
    
    if choice in ("2", "3", "4", "5"):
        print("\n⚠️  Esta funcionalidad avanzada se está integrando.")
        print("   Por ahora, puedes pedirle directamente al agente:")
        if choice == "2": print("   > 'Audita el SEO de https://tuweb.com'")
        if choice == "3": print("   > 'Audita los Meta Ads de [Negocio] en [URL]'")
        if choice == "4": print("   > 'Haz una auditoría de negocio para [Negocio]'")
        if choice == "5": print("   > 'Convierte el instagram @handle en una web'")
        print("\nContinuando con la extracción de leads standard...")
        choice = "1"

    print("\n--- CONFIGURACIÓN DE EXTRACCIÓN ---")

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

    # Goal
    print("\n🎯 ¿Cuál es tu objetivo? (Esto ajusta la puntuación):")
    print("  [1] Vender Diseño Web (puntúa alto si NO tienen web)")
    print("  [2] Vender SEO (puntúa alto si tienen web pero mal SEO)")
    print("  [3] Vender Ads (puntúa alto si tienen web y necesitan tráfico)")
    print("  [4] General (puntúa alto negocios con buena presencia)")
    goal_choice = input("\nElige una opción (1-4, default: 4): ").strip()
    
    goal_map = {"1": "web", "2": "seo", "3": "ads", "4": "general"}
    goal = goal_map.get(goal_choice, "general")

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
    leads = run_pipeline(config, api_key, hunter_key, limit, goal=goal)

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

    # Offer audit
    audit_choice = input("\n¿Auditar websites? (s/n, default: s): ").strip().lower()
    if audit_choice != "n":
        audit_output = output.replace(".csv", "_audit.html")
        generate_audit_report(leads, audit_output)

    print("\n✅ Listo!")



def export_html(leads: List[Dict], output_path: str):
    """Generate a clean HTML report from leads data."""
    tiers_count = {}
    industries_count = {}
    total = len(leads)
    phones = sum(1 for l in leads if l.get("phone"))
    websites = sum(1 for l in leads if l.get("website"))
    with_wa = sum(1 for l in leads if l.get("whatsapp_link"))
    with_booking = sum(1 for l in leads if l.get("booking_links"))
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
        phone = str(l.get("phone", "") or "")
        website = str(l.get("website", "") or "")
        ig = str(l.get("instagram_handle", "") or "")
        fb = str(l.get("facebook_url", "") or "")
        wa = str(l.get("whatsapp_link", "") or "")
        booking = str(l.get("booking_links", "") or "")

        contact_icons = ""
        if phone:
            clean_phone = re.sub(r"[^\d+]", "", phone)
            contact_icons += f'<a href="tel:{html_lib.escape(clean_phone, quote=True)}" class="contact-badge" title="Llamar: {html_lib.escape(phone, quote=True)}">📞</a>'
        if wa:
            contact_icons += f'<a href="{html_lib.escape(wa, quote=True)}" target="_blank" class="contact-badge wa" title="WhatsApp: {html_lib.escape(phone, quote=True)}">💬</a>'
        if website:
            site_url = website if website.startswith("http") else f"https://{website}"
            contact_icons += f'<a href="{html_lib.escape(site_url, quote=True)}" target="_blank" class="contact-badge" title="{html_lib.escape(website, quote=True)}">🌐</a>'
        if ig:
            ig_clean = ig.lstrip("@")
            contact_icons += f'<a href="https://instagram.com/{html_lib.escape(ig_clean, quote=True)}" target="_blank" class="contact-badge" title="Instagram: {html_lib.escape(ig, quote=True)}">📷</a>'
        if fb:
            fb_url = fb if "://" in fb else f"https://{fb}"
            contact_icons += f'<a href="{html_lib.escape(fb_url, quote=True)}" target="_blank" class="contact-badge" title="Facebook: {html_lib.escape(fb, quote=True)}">👍</a>'

        booking_badge = ""
        if booking:
            first_url = booking.split(" | ")[0]
            booking_badge = f'<a href="{html_lib.escape(first_url, quote=True)}" target="_blank" class="booking-badge" title="{html_lib.escape(booking, quote=True)}">📅</a>'

        rows_html += f"""\
<tr>
  <td class="num">{i}</td>
  <td><strong>{html_lib.escape(str(l.get("business_name", "") or ""))}</strong></td>
  <td>{html_lib.escape(str(l.get("industry", "") or ""))}</td>
  <td>{html_lib.escape(str(l.get("city", "") or ""))}</td>
  <td class="contacts">{contact_icons}</td>
  <td class="num">{booking_badge}</td>
  <td class="num">{html_lib.escape(str(rating or ""))}</td>
  <td class="num">{html_lib.escape(str(reviews or ""))}</td>
  <td><span class="tier" style="background:{bg};color:{color};border:1px solid {color}">{tier}</span></td>
  <td class="num"><strong>{html_lib.escape(str(score or ""))}</strong></td>
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
      <div class="ind-name">{html_lib.escape(str(ind_name))}</div>
      <div class="ind-track"><div class="ind-fill" style="width:{pct}%"></div></div>
      <div class="ind-count">{count}</div>
    </div>"""

    # Top Opportunities section (Inspired by kit-prospeccion)
    top_leads = sorted(leads, key=lambda x: x.get("lead_score", 0), reverse=True)[:5]
    top_html = ""
    for lead in top_leads:
        name = html_lib.escape(str(lead.get("business_name", "")))
        score = lead.get("lead_score", 0)
        notes = lead.get("scoring_notes", "No notes")
        phone = lead.get("phone", "")
        email = lead.get("email", "")
        
        # Simple outreach logic
        msg = f"Hola {name}, he visto tu negocio en Google Maps. "
        if "No Website" in notes:
            msg += "He notado que no tienes sitio web, lo que te hace perder visibilidad frente a la competencia..."
        elif "Poor technical SEO" in notes:
            msg += "He analizado tu web y tiene algunos fallos técnicos que impiden que aparezcas en los primeros resultados..."
        else:
            msg += "Me gusta mucho cómo gestionas tu presencia digital, pero creo que podríamos potenciar aún más tus resultados..."

        top_html += f"""
    <div class="opportunity-card">
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
          <h4 style="font-size:16px; margin-bottom:4px;">{name}</h4>
          <div style="font-size:12px; color:#64748b; margin-bottom:8px;">{lead.get("industry", "Unknown")} • {lead.get("city", "")}</div>
        </div>
        <div class="tier" style="background:{tier_bg.get(lead.get("lead_tier", "COLD"), "rgba(0,0,0,0.05)")}; color:{tier_colors.get(lead.get("lead_tier", "COLD"), "#6b7280")}">
          Score: {score}
        </div>
      </div>
      <div style="font-size:13px; margin-bottom:12px; padding:8px; background:#f8fafc; border-radius:6px; border-left:4px solid #3b82f6;">
        <strong>Análisis:</strong> {html_lib.escape(notes)}
      </div>
      <div style="background:#f1f5f9; padding:10px; border-radius:6px; font-size:12px; font-style:italic;">
        <strong>Sugerencia de contacto:</strong> "{msg}"
      </div>
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
.container {{ max-width:1360px; margin:0 auto; padding:24px 20px; }}
.header {{ margin-bottom:28px; }}
.header h1 {{ font-size:28px; font-weight:700; }}
.header p {{ color:#64748b; margin-top:4px; font-size:14px; }}
.stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin-bottom:28px; }}
.stat {{ background:#fff; border-radius:12px; padding:14px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
.stat-value {{ font-size:30px; font-weight:700; }}
.stat-label {{ font-size:12px; color:#64748b; margin-top:2px; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:28px; }}
@media (max-width:768px) {{ .cards {{ grid-template-columns:1fr; }} }}
.card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
.card h3 {{ font-size:15px; font-weight:600; margin-bottom:12px; color:#475569; }}
.ind-bar {{ display:flex; align-items:center; gap:10px; margin-bottom:7px; }}
.ind-name {{ font-size:13px; width:180px; flex-shrink:0; }}
.ind-track {{ flex:1; height:8px; background:#f1f5f9; border-radius:4px; overflow:hidden; }}
.ind-fill {{ height:100%; background:#3b82f6; border-radius:4px; transition:width 0.4s; }}
.ind-count {{ font-size:13px; color:#64748b; width:30px; text-align:right; }}
.table-wrap {{ background:#fff; border-radius:12px; overflow-x:auto; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; min-width:900px; }}
th {{ background:#f8fafc; text-align:left; padding:10px 8px; font-weight:600; color:#475569; border-bottom:2px solid #e2e8f0; white-space:nowrap; }}
td {{ padding:9px 8px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }}
tr:hover {{ background:#fafafa; }}
.num {{ text-align:center; }}
.contacts {{ white-space:nowrap; }}
a.contact-badge {{ text-decoration:none; font-size:16px; margin-right:3px; cursor:pointer; opacity:0.8; transition:opacity 0.15s; display:inline-block; }}
a.contact-badge:hover {{ opacity:1; transform:scale(1.15); }}
.booking-badge {{ text-decoration:none; font-size:16px; cursor:pointer; opacity:0.7; }}
.booking-badge:hover {{ opacity:1; }}
.tier {{ display:inline-block; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; }}
.opportunity-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(350px,1fr)); gap:16px; margin-bottom:28px; }}
.opportunity-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.06); border:1px solid #e2e8f0; }}
.footer {{ text-align:center; padding:24px; color:#94a3b8; font-size:12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 Lead Report</h1>
    <p>{total} leads extraídos • {now} • {phones} con teléfono • {websites} con web • {with_wa} WhatsApp • {with_booking} con reservas • ⭐ {avg_rating:.1f} promedio</p>
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
      <div class="stat-value" style="color:#25D366">{with_wa}</div>
      <div class="stat-label">WhatsApp</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#3b82f6">{websites}</div>
      <div class="stat-label">Con web</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#8b5cf6">{with_booking}</div>
      <div class="stat-label">Sistema reservas</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#f59e0b">{avg_rating:.1f}</div>
      <div class="stat-label">Rating promedio</div>
    </div>
{tiers_html}
  </div>

  <h3 style="margin-bottom:16px; font-size:18px;">🔥 Top 5 Oportunidades</h3>
  <div class="opportunity-grid">
{top_html}
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
          <th class="num">📅</th>
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
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
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
    args = parser.parse_args()

    # Audit mode
    if args.audit:
        if not args.from_csv:
            logger.error("--audit requiere --from-csv <archivo.csv>")
            sys.exit(1)
        leads = load_leads_from_csv(args.from_csv)
        generate_audit_report(leads, args.audit)
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
    leads = run_pipeline(config, api_key, hunter_key, args.limit, goal=args.goal)

    if not leads:
        logger.warning("No leads found. Try expanding keywords or locations.")
        sys.exit(0)

    export_csv(leads, args.output)
    print_summary(leads)

    return leads


if __name__ == "__main__":
    main()
