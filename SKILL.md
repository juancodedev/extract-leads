---
name: lead-extractor
description: >
  Extract, qualify, analyze, and export business leads automatically using Google Places API.
  Use this skill when the user wants to: find leads, build prospect lists, generate sales leads,
  scrape business data from Google Maps, qualify leads by score, audit business websites,
  or create lead reports in CSV/HTML.
  
  Triggers on:
  - "extract leads", "find leads", "get leads", "lead generation", "prospecting"
  - "find prospects", "build lead list", "scrape businesses", "search businesses"
  - "audit websites", "analyze websites", "check websites"
  - "lead report", "lead export", "generate leads"
  - Any mention of Google Maps + leads/prospects/businesses
---

# Lead Extractor Skill

Automatic lead generation for micro-businesses. Searches Google Places, enriches with
WhatsApp/email/social data, scores leads 0-100, audits websites, and exports CSV + HTML reports.

## 🚀 Quick Start (for the AI to execute)

```bash
# 1. Setup
cd /path/to/lead-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Ask for API key, then run
python pipeline.py --interactive
```

## 📋 Workflow — Step by Step

When the user asks for leads, follow this sequence:

### STEP 1: Gather Requirements (ask the user)

Ask these questions one at a time:

1. **¿Qué industrias buscas?** (barberías, cafeterías, servicios profesionales, salud y belleza, retail, fitness, educación, limpieza — o especifica las tuyas)
2. **¿En qué ciudad(es) o región(es)?** (Santiago, Valparaíso, Concepción, o todas)
3. **¿Cuántos leads quieres?** (default 50-100)
4. **¿Tienes API key de Google Places?** (si no, guíalos a https://console.cloud.google.com)
5. **¿Quieres auditar los websites?** (revisa disponibilidad, SEO, booking, imágenes, rendimiento)
6. **¿Quieres reporte HTML además del CSV?**

### STEP 2: Configure & Run

```bash
# Interactive mode (recommended) — asks everything
python pipeline.py --interactive

# Or with direct flags:
export GOOGLE_PLACES_API_KEY="key"
python pipeline.py --limit 100
```

### STEP 3: Show Results

After extraction, show the user:
- Total leads found and by industry
- How many have phone/website/social
- HOT/WARM/COOL breakdown
- Offer to audit websites if not already done

## 📁 Files

| File | Purpose |
|------|---------|
| `pipeline.py` | **Main entry point** — extraction, reports, audit, interactive mode |
| `extractor.py` | Google Places API client |
| `enricher.py` | WhatsApp/Booking/Social detection from website HTML |
| `lead_scorer.py` | Configurable 0-100 scoring engine |
| `analyzer.py` | Website audit (SEO, performance, booking, contact, images, mobile) |
| `config.yaml` | Industries, locations, scoring weights (editable) |
| `requirements.txt` | Dependencies: `requests`, `pyyaml` |

## 🎮 CLI Reference (for the AI)

```bash
# ── Extraction ──────────────────────────────────

# Interactive mode (asks user, then extracts + reports)
python pipeline.py --interactive

# Quick extraction with defaults (uses config.yaml)
python pipeline.py --limit 100

# Custom output
python pipeline.py --output leads.csv --limit 200

# ── Reports ─────────────────────────────────────

# HTML report from existing CSV
python pipeline.py --from-csv leads.csv --html report.html

# ── Website Audit ───────────────────────────────

# Audit all websites from a CSV
python pipeline.py --from-csv leads.csv --audit audit.html
```

## ⚙️ Configuration (`config.yaml`)

The config file defines what to search and how to score:

```yaml
search:
  industries:
    - name: "Barbería y Peluquería"
      keywords: ["barbería", "barber", "peluquería", "salón de belleza"]
      bonus_score: 5
  locations:
    - city: "Santiago"
      region: "Metropolitana"
      premium: true    # gives location bonus in scoring

scoring:
  base_score: 50
  max_score: 100
  weights:
    website: 15
    active_social: 20
    multiple_channels: 10
    premium_location: 10
```

The user can edit this, or use `--interactive` to generate it dynamically.

## 🔍 Website Audit (analyzer.py)

When the user wants to check lead quality, run:

```bash
python pipeline.py --from-csv leads.csv --audit audit.html
```

This analyzes each website for:

| Category | What it checks |
|----------|---------------|
| ✅ Status | HTTP 200, response time, SSL, redirects |
| 📄 SEO | Title, meta description, OG tags, H1, canonical, schema.org, favicon |
| 📅 Booking | AgendaPro, Setmore, TUU, Calendly, Acuity + 15 platforms |
| 🖼️ Images | Count, missing alt attributes, lazy loading |
| 💬 Contact | WhatsApp button, contact form, email/phone links, social links, Google Maps |
| 📱 Mobile | Viewport meta, responsive CSS |
| ⚡ Performance | Gzip, load time, CMS detection |
| 📝 Content | Word count, CTA, testimonials, blog, prices, gallery |

Each site gets a score (0-100) and a list of actionable improvements.

## 📊 Scoring Rubric

| Signal | Points |
|--------|--------|
| Base | 50 |
| Website exists | +15 |
| Active social media | +20 |
| Multiple contact channels (2+) | +10 |
| Premium location | +10 |
| High rating (4.5+) | +5 |
| Industry bonus | +3 to +5 |

**Tiers:** HOT (80-100) → contact now | WARM (60-79) → this week | COOL (40-59) → batch | COLD (<40) → archive

## 📤 Output

**CSV fields:** business_name, industry, phone, email, address, city, website, whatsapp_link, facebook_url, instagram_handle, booking_links, google_rating, review_count, lead_score, lead_tier, scoring_notes.

**HTML report:** interactive table with clickable phone/WhatsApp/website/Instagram/Facebook links and booking system detection.

**Audit HTML:** per-website scorecards with stats and prioritized improvement list.

## 🔐 Required API Keys

| Key | Required | Get it |
|-----|----------|--------|
| `GOOGLE_PLACES_API_KEY` | ✅ Yes | https://console.cloud.google.com (free $200/mo credit) |
| `HUNTER_API_KEY` | Optional | https://hunter.io (for email enrichment) |

## 🌍 Multi-market

The skill is pre-configured for Chile but works anywhere. To change markets:

1. Edit `config.yaml` → change `locations` to your cities/regions
2. Change `industries` keywords to local language
3. Run `python pipeline.py --interactive` or direct

## ❌ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `No module named 'yaml'` | Run `pip install -r requirements.txt` |
| `No Google Places API key` | Set env var or pass `--google-key` |
| `ZERO_RESULTS` | Try broader keywords or different location |
| `REQUEST_DENIED` | API key may not have Places API enabled |
| Site shows 0ms/0 status | Site may be down; verify manually |

## 📦 Package Structure (for distribution)

```
lead-extractor/
├── SKILL.md              ← This file (agent instructions)
├── pipeline.py           ← Main CLI
├── extractor.py          ← Google Places search
├── enricher.py           ← Social/WhatsApp/Booking detection
├── lead_scorer.py        ← Scoring engine
├── analyzer.py           ← Website audit
├── config.yaml           ← User configuration
├── requirements.txt      ← Python deps
├── README.md             ← GitHub readme
└── files/                ← Original reference docs
```
