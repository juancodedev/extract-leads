"""
Summary and HTML report generation for lead data.
"""
import html as html_lib
import logging
import os
import re
from datetime import datetime
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader

from analyzer import (
    MAX_IMPROVEMENTS,
    TECH_BASE_SCORE,
    TECH_GREEN_THRESHOLD,
    TECH_MAX_SCORE,
    TECH_YELLOW_THRESHOLD,
)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

logger = logging.getLogger(__name__)


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


def export_html(leads: List[Dict], output_path: str):
    """Generate a clean HTML report from leads data."""
    # Sort leads by score descending
    leads = sorted(leads, key=lambda x: x.get("lead_score", 0), reverse=True)

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

    rows = []
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
            contact_icons += f'<a href="tel:{html_lib.escape(clean_phone, quote=True)}" class="contact-badge" style="color: #475569;" title="Llamar: {html_lib.escape(phone, quote=True)}"><span class="material-icons">phone</span></a>'
        if wa:
            contact_icons += f'<a href="{html_lib.escape(wa, quote=True)}" target="_blank" class="contact-badge" style="color: #25D366;" title="WhatsApp: {html_lib.escape(phone, quote=True)}"><span class="material-icons">whatsapp</span></a>'
        if website:
            site_url = website if website.startswith("http") else f"https://{website}"
            contact_icons += f'<a href="{html_lib.escape(site_url, quote=True)}" target="_blank" class="contact-badge" style="color: #3b82f6;" title="{html_lib.escape(website, quote=True)}"><span class="material-icons">language</span></a>'
        if ig:
            ig_clean = ig.lstrip("@")
            contact_icons += f'''<a href="https://instagram.com/{html_lib.escape(ig_clean, quote=True)}" target="_blank" class="contact-badge" style="color: #E1306C;" title="Instagram: {html_lib.escape(ig, quote=True)}">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8A3.6 3.6 0 0 0 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6A3.6 3.6 0 0 0 16.4 4H7.6m9.65 1.5a1.25 1.25 0 0 1 1.25 1.25A1.25 1.25 0 0 1 17.25 8 1.25 1.25 0 0 1 16 6.75a1.25 1.25 0 0 1 1.25-1.25M12 7a5 5 0 0 1 5 5 5 5 0 0 1-5 5 5 5 0 0 1-5-5 5 5 0 0 1 5-5m0 2a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3z"/></svg>
            </a>'''
        if fb:
            fb_url = fb if "://" in fb else f"https://{fb}"
            contact_icons += f'<a href="{html_lib.escape(fb_url, quote=True)}" target="_blank" class="contact-badge" style="color: #1877F2;" title="Facebook: {html_lib.escape(fb, quote=True)}"><span class="material-icons">facebook</span></a>'

        booking_badge = ""
        if booking:
            first_url = booking.split(" | ")[0]
            booking_badge = f'<a href="{html_lib.escape(first_url, quote=True)}" target="_blank" class="booking-badge" style="color: #8b5cf6;" title="{html_lib.escape(booking, quote=True)}"><span class="material-icons">event_available</span></a>'

        rows.append({
            "num": i,
            "name": str(l.get("business_name", "") or ""),
            "industry": str(l.get("industry", "") or ""),
            "city": str(l.get("city", "") or ""),
            "contacts_html": contact_icons,
            "booking_badge": booking_badge,
            "rating": str(rating or ""),
            "reviews": str(reviews or ""),
            "tier": tier,
            "tier_color": color,
            "tier_bg": bg,
            "score": score,
        })

    tiers = []
    for t in ["HOT", "WARM", "COOL", "COLD"]:
        c = tiers_count.get(t, 0)
        if c:
            pct = c * 100 // total
            tiers.append({"name": t, "count": c, "pct": pct, "color": tier_colors[t]})

    industries = []
    for ind_name, count in sorted(industries_count.items(), key=lambda x: -x[1]):
        pct = count * 100 // total
        industries.append({"name": str(ind_name), "count": count, "pct": pct})

    # Top Opportunities section (Inspired by kit-prospeccion)
    top_leads = leads[:5]
    top_opportunities = []
    for lead in top_leads:
        raw_name = str(lead.get("business_name", ""))
        score = lead.get("lead_score", 0)
        notes = lead.get("scoring_notes", "No notes")

        # Simple outreach logic
        msg = f"Hola {raw_name}, he visto tu negocio en Google Maps. "
        if "No Website" in notes:
            msg += "He notado que no tienes sitio web, lo que te hace perder visibilidad frente a la competencia..."
        elif "Poor technical SEO" in notes:
            msg += "He analizado tu web y tiene algunos fallos técnicos que impiden que aparezcas en los primeros resultados..."
        else:
            msg += "Me gusta mucho cómo gestionas tu presencia digital, pero creo que podríamos potenciar aún más tus resultados..."

        # Specialized audit badges (raw HTML, pass with |safe in template)
        audit_badges = ""
        if lead.get("audit_data"):
            audit_badges += '<span class="tier" style="background:rgba(59,130,246,0.1); color:#3b82f6; border:1px solid #3b82f6; margin-right:4px;">SEO Auditado</span>'
        if lead.get("requires_ads_audit"):
            audit_badges += '<span class="tier" style="background:rgba(139,92,246,0.1); color:#8b5cf6; border:1px solid #8b5cf6; margin-right:4px;">Meta Ads Ready</span>'
        if lead.get("requires_ig_web_prototype"):
            audit_badges += '<span class="tier" style="background:rgba(225,48,108,0.1); color:#E1306C; border:1px solid #E1306C; margin-right:4px;">IG-to-Web Ready</span>'

        top_opportunities.append({
            "name": raw_name,
            "industry": str(lead.get("industry", "Unknown")),
            "city": str(lead.get("city", "")),
            "score": score,
            "notes": notes,
            "audit_badges": audit_badges,
            "tier": lead.get("lead_tier", "COLD"),
            "tier_color": tier_colors.get(lead.get("lead_tier", "COLD"), "#6b7280"),
            "tier_bg": tier_bg.get(lead.get("lead_tier", "COLD"), "rgba(0,0,0,0.05)"),
            "suggested_msg": msg,
        })

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    template = jinja_env.get_template("lead_report.html")
    html = template.render(
        total=total,
        phones=phones,
        websites=websites,
        with_wa=with_wa,
        with_booking=with_booking,
        avg_rating=avg_rating,
        now=now,
        tiers=tiers,
        industries=industries,
        rows=rows,
        top_opportunities=top_opportunities,
    )

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Reporte HTML generado: %s", output_path)


def export_audit_html(results: List[Dict], output_path: str, total_leads: int, audited: int):
    """Generate the website audit HTML report from analysis results."""
    results = sorted(
        results,
        key=lambda x: (x.get("lead_score", 0), x.get("business_name", "")),
        reverse=True,
    )

    ok_sites = sum(1 for r in results if r.get("status") == "ok")
    error_sites = sum(1 for r in results if r.get("error"))
    avg_rt = 0
    if results:
        rt_sum = sum(r.get("response_time_ms", 0) for r in results if r.get("status") == "ok")
        avg_rt = rt_sum // max(ok_sites, 1)

    score_bg = {
        "✅": "#dcfce7",
        "⚠️": "#fef3c7",
        "❌": "#fee2e2",
        "🔒": "#fef3c7", "🔗": "#fef3c7", "📄": "#fef3c7",
        "📝": "#fef3c7", "🖼️": "#fef3c7", "📑": "#fef3c7",
        "📱": "#fef3c7", "💬": "#fef3c7", "📅": "#e0f2fe",
        "🎯": "#fef3c7", "⭐": "#fef3c7", "📰": "#fef3c7",
        "💰": "#fef3c7", "🏗️": "#fef3c7", "⚡": "#dcfce7",
        "🐌": "#fee2e2", "🗜️": "#fef3c7", "📸": "#fef3c7",
        "📍": "#fef3c7", "🏷️": "#fef3c7", "📊": "#fef3c7",
        "⏱️": "#fef3c7",
    }

    cards = []
    for r in results:
        name = str(r.get("business_name", "") or "")
        status = r.get("status", "error")
        code = r.get("status_code", 0)
        rt = r.get("response_time_ms", 0)
        ssl = r.get("ssl", False)
        url = str(r.get("url_clean", "") or "")
        tech = ", ".join(str(t) for t in r.get("tech_stack", []))
        booking = r.get("booking", {})
        booking_str = ", ".join(booking.get("systems", [])) if booking and booking.get("has_booking") else "No detectado"
        images = r.get("images", {})
        seo = r.get("seo", {})
        contact = r.get("contact", {})
        content = r.get("content", {})
        mobile = r.get("mobile", {})
        improvements = r.get("improvements", [])

        status_emoji = "✅" if status == "ok" else ("⚠️" if code else "❌")
        status_color = "#22c55e" if status == "ok" else ("#f59e0b" if code else "#ef4444")

        # Technical Score
        tech_score = TECH_BASE_SCORE
        if status == "ok": tech_score += 15
        if ssl: tech_score += 5
        if rt < 1500: tech_score += 5
        if seo.get("has_title"): tech_score += 4
        if seo.get("has_meta_description"): tech_score += 4
        if seo.get("has_og_title"): tech_score += 3
        if seo.get("has_canonical"): tech_score += 2
        if seo.get("has_h1"): tech_score += 3
        if seo.get("has_favicon"): tech_score += 2
        if seo.get("has_schema_org"): tech_score += 3
        if images.get("total", 0) > 0: tech_score += 3
        if images.get("without_alt", 0) == 0 and images.get("total", 0) > 0: tech_score += 3
        if images.get("has_lazy_loading"): tech_score += 2
        if mobile.get("has_viewport"): tech_score += 4
        if contact.get("has_whatsapp"): tech_score += 4
        if contact.get("has_contact_form"): tech_score += 3
        if content.get("has_cta"): tech_score += 3
        if content.get("has_testimonials"): tech_score += 2
        if booking.get("has_booking"): tech_score += 3
        tech_score = min(tech_score, TECH_MAX_SCORE)

        tech_score_color = (
            "#22c55e" if tech_score >= TECH_GREEN_THRESHOLD
            else ("#f59e0b" if tech_score >= TECH_YELLOW_THRESHOLD else "#ef4444")
        )

        lead_score = r.get("lead_score", 0)
        lead_tier = r.get("lead_tier", "COLD")
        tier_colors = {"HOT": "#ef4444", "WARM": "#f59e0b", "COOL": "#3b82f6", "COLD": "#6b7280"}
        lead_color = tier_colors.get(lead_tier, "#6b7280")

        imgs_html = f"{images.get('total', 0)} imágenes"
        if images.get("without_alt", 0) > 0:
            imgs_html += f", {images['without_alt']} sin alt"

        contact_icons = ""
        if contact.get("has_whatsapp"): contact_icons += "💬 "
        if contact.get("has_phone_link"): contact_icons += "📞 "
        if contact.get("has_contact_form"): contact_icons += "📝 "
        if contact.get("has_email_link"): contact_icons += "📧 "
        if contact.get("has_google_maps_embed"): contact_icons += "📍 "

        mobile_str = "Responsive" if mobile.get("has_viewport") else "No responsive"
        seo_title = str(seo.get("title", "Sin title") or "Sin title")[:40]
        industry = str(r.get("industry", "") or "")
        city = str(r.get("city", "") or "")
        phone = str(r.get("phone", "") or "")

        cards.append({
            "name": name,
            "url": url,
            "industry": industry,
            "city": city,
            "phone": phone,
            "score": tech_score,
            "score_color": tech_score_color,
            "status_emoji": status_emoji,
            "status_color": status_color,
            "code": code,
            "rt": rt,
            "ssl": ssl,
            "booking_str": booking_str,
            "imgs_html": imgs_html,
            "mobile_str": mobile_str,
            "tech": tech,
            "contact_icons": contact_icons,
            "seo_title": seo_title,
            "improvements": improvements[:MAX_IMPROVEMENTS],
            "lead_tier": lead_tier,
            "lead_color": lead_color,
            "lead_score": lead_score,
        })

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    with_booking = sum(1 for r in results if r.get("booking", {}).get("has_booking"))
    with_whatsapp = sum(1 for r in results if r.get("contact", {}).get("has_whatsapp"))

    template = jinja_env.get_template("audit_report.html")
    html = template.render(
        audited=audited,
        total_leads=total_leads,
        now=now,
        ok_sites=ok_sites,
        error_sites=error_sites,
        avg_rt=avg_rt,
        with_booking=with_booking,
        with_whatsapp=with_whatsapp,
        cards=cards,
        score_bg=score_bg,
    )

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Auditoría generada: %s", output_path)
