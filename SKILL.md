---
name: lead-extractor
description: >
  Extract, qualify, analyze, and export business leads automatically.
  Includes advanced audits (SEO, Meta Ads, Business) and Instagram-to-Web conversion.
  Use this skill for: finding leads, prospecting, competitive analysis, website audits,
  Meta Ads audits, and building personal brand sites from Instagram.
  
  Triggers on:
  - "extract leads", "find leads", "prospecting", "find prospects"
  - "audit website", "SEO audit", "Meta Ads audit", "business audit"
  - "instagram to web", "brand website", "convert instagram"
  - "lead report", "lead generation", "analyze business"
---

# Lead Extractor & Business Auditor Skill

Advanced lead generation and digital auditing. Searches Google Places, enriches data, scores leads, and performs deep audits (SEO, Ads, Business) to generate high-value reports.

## 🚀 Capabilities

### 1. Lead Extraction (Multi-Source)
- **Google Places**: High-volume extraction using API.
- **Manual Search**: Deep search for specific niches using WebSearch/WebFetch.
- **Enrichment**: WhatsApp, Social Media, and Hunter.io email detection.
- **Scoring**: 0-100 opportunity score based on digital gaps.

### 2. Specialized Audits (HTML Reports)
- **SEO Audit**: Deep technical analysis (Meta tags, Headings, Schema, Speed, Social).
- **Meta Ads Audit**: Analysis of active ads in Meta Library vs. Landing page coherence.
- **Business Audit**: Holistic view (Web, Social, Pricing, Offer, Customer Journey, Google Business).

### 3. Personal Brand (Instagram → Web)
- Converts an Instagram profile into a professional personal brand website.
- Extracts bio, stats, and recent photos to create a premium landing page.

---

## 📋 Workflows

### 🔍 Workflow A: Lead Generation & Prospecting
1. **Gather Requirements**: Industry, Location, Volume, and Goal (Selling Web, SEO, Ads, etc.).
2. **Search**: Use Google Places API for volume. Use WebSearch for niche/directory scraping.
3. **Analyze**: Check website availability, SEO signals, and social activity.
4. **Score**: Calculate opportunity score (e.g., higher score if missing web or SEO is poor).
5. **Report**: Generate CSV and a **Visual HTML Dashboard** with prioritized leads.

### 🛠 Workflow B: Advanced SEO Audit
1. **Analyze**: Extract meta tags, h1-h6 structure, images/alt, schema, and performance.
2. **Check**: Verify robots.txt, sitemap.xml, and HTTPS.
3. **Score**: Grade categories (Meta, Technical, Content, Social).
4. **Deliver**: HTML file `auditoria-seo-[domain].html` with top 5 prioritized fixes.

### 📢 Workflow C: Meta Ads Audit
1. **Search**: Find active ads in Meta Ads Library for the business.
2. **Compare**: Check "Message Match" between Ads and Landing Pages.
3. **Analyze**: Review copy, creative hooks, and CTA effectiveness.
4. **Deliver**: HTML file `auditoria-meta-ads-[name].html` with new ad copy suggestions.

### 💼 Workflow D: Digital Business Audit
1. **Investigate**: Web presence, Social Media activity, and Google Business profile.
2. **Review**: Analyze product/service offer, pricing consistency, and sales funnel.
3. **Competitors**: Compare against 1-2 key competitors.
4. **Deliver**: HTML file `auditoria-negocio-[name].html` with a prioritized action plan.

### 📸 Workflow E: Instagram → Web
1. **Extract**: Profile info, stats, and top 6-12 post images from Instagram.
2. **Design**: Create a premium HTML site reflecting the brand's personality.
3. **Deliver**: `web-[handle].html` with interactive scroll effects and IG-style hero.

---

## 🎮 CLI Reference

```bash
# ── Standard Pipeline ───────────────────────────
python pipeline.py --interactive

# ── SEO Audit ───────────────────────────────────
# (Use the agent's internal SEO audit logic)
"Audit SEO for https://example.com"

# ── Meta Ads Audit ──────────────────────────────
"Audit Meta Ads for [Business Name] and [URL]"

# ── Business Audit ──────────────────────────────
"Perform a full business audit for [Business Name]"

# ── Instagram to Web ────────────────────────────
"Convert @handle into a personal brand website"
```

## 📁 Directory Structure
- `pipeline.py`: Main orchestration.
- `analyzer.py`: Technical website analysis.
- `extractor.py`: Google Places integration.
- `enricher.py`: Data enrichment (Social/Email).
- `agents/`: Specialized skill templates (SEO, Ads, Business, IG).


```bash
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
