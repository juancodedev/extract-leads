# Lead Extractor

Automatic lead generation for micro-businesses using Google Places API.

## Files

| File | Purpose |
|------|---------|
| `pipeline.py` | CLI entry point — runs the full extraction |
| `extractor.py` | Searches Google Places for businesses |
| `enricher.py` | Finds emails + social media from websites |
| `lead_scorer.py` | Scores and tiers leads |
| `config.yaml` | Your target industries, locations, scoring rules |
| `requirements.txt` | Python dependencies |
| `files/` | Original reference documentation (manual research guides) |

## Setup

```bash
pip install -r requirements.txt
export GOOGLE_PLACES_API_KEY="your_key"
```

Optional for email enrichment:

```bash
export HUNTER_API_KEY="your_key"
```

## Usage

```bash
# Run with default config (config.yaml)
python pipeline.py

# Limit to 50 leads
python pipeline.py --limit 50

# Custom output
python pipeline.py --output my_leads.csv

# Custom config
python pipeline.py --config my_business.yaml
```

## Configuring for Your Business

Edit `config.yaml`:

- **industries**: business types to search for + keywords per type
- **locations**: cities and regions, mark as `premium: true` for score bonus
- **scoring.weights**: adjust how many points each signal is worth
- **scoring.tiers**: define score ranges for HOT/WARM/COOL/COLD

## Output

CSV file with: business_name, industry, phone, email, address, city, website, social links, rating, lead_score, lead_tier.

## Requirements

- Python 3.8+
- Google Places API key (free tier: $200/mo credit)
- Optional: Hunter.io API key for email enrichment
