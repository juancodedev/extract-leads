"""
Summary and HTML report generation for lead data.
"""
import html as html_lib
import logging
import os
import re
from datetime import datetime
from typing import Dict, List

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
    top_leads = leads[:5]
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

        # Specialized audit badges
        audit_badges = ""
        if lead.get("audit_data"):
            audit_badges += '<span class="tier" style="background:rgba(59,130,246,0.1); color:#3b82f6; border:1px solid #3b82f6; margin-right:4px;">SEO Auditado</span>'
        if lead.get("requires_ads_audit"):
            audit_badges += '<span class="tier" style="background:rgba(139,92,246,0.1); color:#8b5cf6; border:1px solid #8b5cf6; margin-right:4px;">Meta Ads Ready</span>'
        if lead.get("requires_ig_web_prototype"):
            audit_badges += '<span class="tier" style="background:rgba(225,48,108,0.1); color:#E1306C; border:1px solid #E1306C; margin-right:4px;">IG-to-Web Ready</span>'

        top_html += f"""
    <div class="opportunity-card">
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
          <h4 style="font-size:16px; margin-bottom:4px;">{name}</h4>
          <div style="font-size:12px; color:#64748b; margin-bottom:8px;">{lead.get("industry", "Unknown")} • {lead.get("city", "")}</div>
          <div style="margin-bottom:8px;">{audit_badges}</div>
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
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
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
a.contact-badge {{ text-decoration:none; margin-right:6px; cursor:pointer; opacity:0.8; transition:all 0.15s; display:inline-flex; align-items:center; vertical-align:middle; }}
a.contact-badge:hover {{ opacity:1; transform:scale(1.2); }}
.material-icons {{ font-size: 20px; }}
.booking-badge {{ text-decoration:none; cursor:pointer; opacity:0.7; display:inline-flex; align-items:center; vertical-align:middle; }}
.booking-badge:hover {{ opacity:1; transform:scale(1.2); }}
.tier {{ display:inline-block; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600; }}
.opportunity-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(350px,1fr)); gap:16px; margin-bottom:28px; }}
.opportunity-card {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.06); border:1px solid #e2e8f0; }}
.ranking-legend {{ background:#fff; border-radius:12px; padding:20px; margin-bottom:28px; box-shadow:0 1px 3px rgba(0,0,0,0.06); border-left:4px solid #3b82f6; }}
.ranking-legend h3 {{ font-size:16px; margin-bottom:10px; color:#1e293b; }}
.ranking-legend p {{ font-size:13px; color:#64748b; line-height:1.5; margin-bottom:12px; }}
.tier-legend {{ display:flex; gap:12px; flex-wrap:wrap; }}
.tier-item {{ display:flex; align-items:center; gap:6px; font-size:12px; }}
.footer {{ text-align:center; padding:24px; color:#94a3b8; font-size:12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1 style="display:flex; align-items:center; gap:10px;"><span class="material-icons" style="font-size:32px; color:#3b82f6;">analytics</span> Lead Report</h1>
    <p>{total} leads extraídos • {now} • {phones} con teléfono • {websites} con web • {with_wa} WhatsApp • {with_booking} con reservas • {avg_rating:.1f} rating promedio</p>
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

  <div class="ranking-legend">
    <h3>¿Qué significa el Ranking?</h3>
    <p>El <strong>Lead Score</strong> (0-100) mide el potencial de conversión y la necesidad de servicios digitales. Se calcula analizando la presencia de sitio web, redes sociales activas, canales de contacto, ubicación premium y deficiencias técnicas que representan una oportunidad de venta.</p>
    <div class="tier-legend">
      <div class="tier-item"><span class="tier" style="background:{tier_bg['HOT']}; color:{tier_colors['HOT']}; border:1px solid {tier_colors['HOT']}">HOT (80-100)</span> <span>Alta prioridad: Necesidad crítica o encaje perfecto.</span></div>
      <div class="tier-item"><span class="tier" style="background:{tier_bg['WARM']}; color:{tier_colors['WARM']}; border:1px solid {tier_colors['WARM']}">WARM (60-79)</span> <span>Interés alto: Buen prospecto con margen de mejora.</span></div>
      <div class="tier-item"><span class="tier" style="background:{tier_bg['COOL']}; color:{tier_colors['COOL']}; border:1px solid {tier_colors['COOL']}">COOL (40-59)</span> <span>Interés medio: Requiere más trabajo de educación.</span></div>
      <div class="tier-item"><span class="tier" style="background:{tier_bg['COLD']}; color:{tier_colors['COLD']}; border:1px solid {tier_colors['COLD']}">COLD (0-39)</span> <span>Baja prioridad: Poco encaje o ya bien servido.</span></div>
    </div>
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
          <th class="num"><span class="material-icons" style="font-size:18px;">event_available</span></th>
          <th class="num"><span class="material-icons" style="font-size:18px;">star</span></th>
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
