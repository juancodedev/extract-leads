---
name: lead-extractor
description: Extract, qualify, and structure leads from micro-businesses using Google Places API. Use this skill when the user wants to automatically find leads matching configured industries and locations. Supports scoring, enrichment (email via Hunter.io, social media detection), and CSV export. Triggers on: "extract leads", "build lead list", "find prospects", "lead generation", "prospecting".
---

# Lead Extractor Skill

A fully automated skill for finding, qualifying, and exporting business leads via the Google Places API.

## Architecture

```
config.yaml          ← Your business profile (industries, locations, scoring rules)
extractor.py         ← Google Places API client (text search + details)
enricher.py          ← Hunter.io email lookup + social media detection from websites
lead_scorer.py       ← Configurable scoring engine (0-100 pts)
pipeline.py          ← CLI orchestrator that runs the full flow
leads_output/        ← Generated CSV exports
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Google Places API key
export GOOGLE_PLACES_API_KEY="your_key_here"

# 3. Run the pipeline
python pipeline.py

# Output: leads_output/leads.csv with scored leads
```

## How It Works

1. **Search** — For each industry keyword × location in `config.yaml`, the extractor queries Google Places Text Search API
2. **Detail fetch** — Each business result is enriched with phone, website, rating via Place Details API
3. **Enrich** — If Hunter.io key is set, emails are looked up; website HTML is scanned for social media links
4. **Score** — Configurable 0-100 rubric applied (digital presence, channels, location, rating)
5. **Export** — CSV with all fields + score + tier (HOT/WARM/COOL/COLD)

## Configuration

Edit `config.yaml` to define:

| Section | What to configure |
|---------|------------------|
| `search.industries` | Business types to target + keywords per type |
| `search.locations` | Cities/regions with premium flag |
| `scoring.weights` | Point values for each signal (website, social, etc.) |
| `scoring.tiers` | Score ranges for HOT/WARM/COOL/COLD |

## Scoring Rubric

| Signal | Points |
|--------|--------|
| Base | 50 |
| Website exists | +15 |
| Active social media | +20 |
| Multiple contact channels (2+) | +10 |
| Premium location | +10 |
| High rating (4.5+) | +5 |
| Industry bonus | +3 to +5 |
| Owner info available | +5 |

## Output Fields

business_name, industry, phone, email, address, city, website, facebook_url, instagram_handle, google_rating, review_count, lead_score, lead_tier, source, date_found
