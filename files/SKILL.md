---
name: chile-lead-extractor
description: Extract, qualify, and structure leads from Chilean micro-businesses (1-10 employees) for technology solutions. Use this skill when the user wants to build a lead list from Google Maps, Facebook, Instagram, local directories, or other sources targeting SMEs in service, retail, food & beverage, or professional services. Automatically score leads by fit, collect essential contact info, and export in structured format. Triggers on: "extract leads", "build lead list", "qualify leads Chile", "find prospects Chile", "scrape businesses", "lead generation", "prospecting", or when the user mentions specific channels (Google Maps, Facebook, directories) for finding Chilean businesses.
---

# Chile Lead Extractor

A comprehensive skill for finding, qualifying, and structuring high-quality leads from Chilean micro-businesses targeting technology solutions for process automation, scheduling, inventory, and financial management.

---

## What This Skill Does

This skill automates and guides the process of:

1. **Identifying prospects** across multiple channels (Google Maps, Facebook, Instagram, local directories)
2. **Collecting essential data** (name, phone, email, industry, location, social profiles)
3. **Scoring leads** based on tech-readiness, pain points, and engagement signals
4. **Exporting structured data** in CSV/JSON format for CRM integration or outreach campaigns

---

## When to Use This Skill

Use this skill when:

- You're building a prospecting pipeline for Chilean SMEs
- You want to systematize lead qualification with scoring
- You need to extract and structure contact information from various sources
- You're testing product-market fit with automated outreach
- You want to expand geographically (Santiago → other regions → LATAM)

**Do NOT use this skill for:**
- Large enterprises (11+ employees)
- Regulated industries (banking, insurance, medical)
- Markets outside your target (non-Chile for Phase 1)

---

## How to Use This Skill

### 1. **Define Your Search Parameters**

Start by specifying:
- **Industry focus** (barbershops, cafés, accountants, online retailers, etc.)
- **Geographic area** (Santiago neighborhoods, regions, or specific cities)
- **Lead source** (Google Maps, Facebook, directories, social media)
- **Tech-readiness preference** (prefer businesses with websites/social presence?)

### 2. **Run Structured Search**

The skill guides you through:

**Option A: Manual Lead Entry**
- Enter leads manually from your searches
- Skill extracts and validates each entry
- Checks for duplicate/duplicate-like entries

**Option B: Guided Research**
- Skill suggests search queries for your target industry + location
- Provides search tips for each channel
- Helps you compile findings into structured format

**Option C: Batch Processing**
- Upload a list of leads (CSV/JSON)
- Skill cleans, deduplicates, and enriches data
- Validates phone numbers and email formats

### 3. **Qualify with Lead Scoring**

The skill applies a **0-100 point scoring system**:

**Must-Have Criteria (Disqualifying):**
- ✓ Located in target region
- ✓ 1-10 employees (microenterprise)
- ✓ Active business (recent posts/updates)

**Priority Factors:**
- Active social media (Instagram/Facebook): +20 pts
- Website or online presence: +15 pts
- Clear pain point signals (reviews/posts): +15 pts
- Uses WhatsApp Business: +10 pts
- Multiple contact channels: +10 pts
- Owner/founder info accessible: +10 pts

**Scoring Thresholds:**
- **80-100 pts:** Immediate outreach (hot leads)
- **60-79 pts:** Primary queue (warm leads)
- **40-59 pts:** Secondary queue (worth trying)
- **<40 pts:** Archive or manual review

### 4. **Export and Organize**

The skill produces:

```
LEAD EXPORT FORMATS:

📊 CSV (for spreadsheet/CRM import)
├── Lead ID | Business Name | Industry | Contact Person
├── Phone | Email | City | Website
├── Social Media (Facebook/Instagram/LinkedIn)
├── Estimated Employees | Tech-Readiness Score
├── Primary Pain Point | Last Updated | Outreach Status

📋 JSON (for app integration)
├── Structured nested format
├── Includes scoring rationale
├── Ready for API/database insertion

📱 WhatsApp List
├── Formatted phone numbers with country code (+56)
├── Business name and industry notes

📧 Email Campaign List
├── Validated emails with business context
├── Pre-drafted personalization variables
```

---

## Essential Data to Collect

### **MUST-HAVE (Always Required)**

| Field | Example | Why |
|-------|---------|-----|
| **Business Name** | Barbería Los Condes | Verification & personalization |
| **Industry** | Barbershop/Service | Determine fit |
| **Contact Person** | Juan García (owner) | Personal outreach |
| **Phone** | +56 9 8765 4321 | Primary contact method |
| **City** | Santiago / Las Condes | Geographic targeting |
| **Source** | Google Maps | Track channel effectiveness |

### **SHOULD-HAVE (High Priority)**

| Field | Example | Use |
|-------|---------|-----|
| **Email** | juan@barberia.cl | Formal follow-up |
| **Website** | www.barberia-loscones.cl | Tech-readiness signal |
| **Facebook** | facebook.com/barberia.loscones | Engagement tracking |
| **Instagram** | @barberia_loscones | Visual presence, DM channel |
| **Employee Estimate** | 2-5 | Operational complexity |

### **NICE-TO-HAVE (Enrichment)**

| Field | Example | Use |
|-------|---------|-----|
| **Google Rating** | 4.7/5 (45 reviews) | Credibility signal |
| **Years Operating** | 2018-present | Stability indicator |
| **Operating Hours** | Mon-Sat 9am-7pm | Best contact time |
| **Pain Point Signals** | "Hard to book appointments" | Pitch personalization |
| **Current Tools** | Excel, WhatsApp, Instagram | Integration gaps |

---

## Lead Filtering Rules

### **INCLUDE (Target These)**

**By Size:**
- 1-10 employees
- Independent sole proprietors
- Owner-operated businesses

**By Industry (Priority):**
1. **Service Sector:** Barbershops, salons, massage, accountants, lawyers, cleaning
2. **Retail/Commerce:** Mini-markets, hardware stores, online shops
3. **Food & Beverage:** Cafés, restaurants, bakeries
4. **Professional Services:** Consultants, freelancers, trainers

**By Digital Maturity:**
- ✅ Active social media (posts in last 30 days)
- ✅ Website or online presence
- ✅ Business WhatsApp or messaging
- ✅ Uses payment systems (Khipu, Stripe, etc.)

**By Geography (Phase-Based):**
- **Phase 1 (Now):** Santiago Metropolitan Region
- **Phase 2 (3-6 mo):** Valparaíso, Biobío, Los Ríos
- **Phase 3 (6-12 mo):** Full Chile + LATAM expansion

### **EXCLUDE (Avoid These)**

- ❌ 11+ employees / >USD 5M revenue
- ❌ Regulated industries (banking, pharmaceutical, medical)
- ❌ Large corporations with IT departments
- ❌ Closed/defunct businesses
- ❌ No phone or digital presence
- ❌ Consistently negative reviews/spam indicators

---

## Workflow: Step-by-Step

### **Workflow 1: Manual Research + Extraction**

```
PHASE 0 (Quick Wins - This Week):

Day 1: Google Maps Deep Dive
├─ Search 3 industries + location (e.g., "barbershop Santiago")
├─ Extract 15-20 leads per search
├─ Collect: name, phone, website, address, reviews summary
└─ Time: 1-2 hours → ~30-50 leads

Day 2: Facebook + Instagram
├─ Search business pages + hashtags
├─ Check contact info in bio (email, WhatsApp, website)
├─ Assess engagement level (posting frequency)
└─ Time: 1-1.5 hours → ~20-30 leads

Day 3: Directory Mining
├─ PáginsAmarillas.cl (Yellow Pages)
├─ Cámaras de Comercio (Chamber directories)
├─ Mercado Público (Government registry)
└─ Time: 1-2 hours → ~50-100 leads

TOTAL: 3-4 hours research → 100-180 leads
```

### **Workflow 2: Batch Import + Scoring**

```
PHASE 1 (Structuring & Qualification):

Step 1: Import Raw Leads
├─ Upload CSV with business names + phone/source
├─ Skill validates format and deduplicates

Step 2: Auto-Enrichment
├─ Skill suggests data fields to research
├─ Prompts for: website, social media, employee count
├─ Identifies pain point signals from available info

Step 3: Lead Scoring
├─ Applies 0-100 point rubric
├─ Flags high-priority leads (80+)
├─ Groups by score tier for prioritized outreach

Step 4: Export
├─ CSV for spreadsheet
├─ JSON for CRM/API
├─ WhatsApp list for direct messaging
└─ Time: 30 mins setup + 2-3 hours research/enrichment
```

### **Workflow 3: Outreach Preparation**

```
PHASE 2 (Campaign Readiness):

Step 1: Segment by Industry
├─ Group leads: Barbershops, Cafés, Accountants, etc.
├─ Enables industry-specific messaging

Step 2: Segment by Channel
├─ WhatsApp-enabled (has business number)
├─ Email-only (no phone)
├─ Call-only (phone no email/social)

Step 3: Generate Outreach Templates
├─ Industry-specific pain point angles
├─ Channel-appropriate messaging (WhatsApp < 1500 chars)
├─ A/B test versions for different score tiers

Step 4: Track & Report
├─ Response rates by channel
├─ Industry conversion funnel
├─ Geographic hotspots
└─ Iterate messaging based on learnings
```

---

## Search Channel Tactics (Quick Reference)

### **Google Maps (Best Starting Point)**

```
Search queries:
├─ "[Industry] [City]" → "barbershop Santiago", "café Las Condes"
├─ "[Industry] [Neighborhood]" → "peluquería Ñuñoa"
├─ Zoom to specific areas on map

Extract:
├─ Business name, phone, website, address
├─ Review count + rating (engagement signal)
├─ Operating hours
├─ Link to website (validate with Hunter.io if email needed)

Time per search: 15-20 mins = 15-20 leads
```

### **Facebook (High Adoption in Chile)**

```
Search tactics:
├─ Search bar: "[Industry] [City]" hashtags
├─ Hashtags: #peluqueriasantiago, #barbershopsantiago
├─ Browse business pages, check activity

Extract:
├─ Business page URL, posting frequency
├─ Contact info in "About" section (email, phone, WhatsApp)
├─ Engagement metrics (likes, comments, shares on recent posts)

Time per search: 20-30 mins = 20-30 leads
```

### **Instagram (Visual + High Engagement)**

```
Search tactics:
├─ Search hashtags: #peluqueriachile, #cafésantiago
├─ Geotag search: Search location "Santiago"
├─ Browse business profiles with contact info in bio

Extract:
├─ Business handle, follower count, post frequency
├─ Contact info (email, WhatsApp link, website)
├─ DM option available (engagement channel)

Time per search: 15-20 mins = 15-20 leads
```

### **Directories (Curated, Semi-Automated)**

```
PáginsAmarillas.cl (Yellow Pages):
├─ Category search: "Peluquerías", "Barbershops", "Cafeterías"
├─ Filter by location
├─ Extract: name, phone, address
└─ Time: 30-45 mins = 50+ leads

Cámaras de Comercio:
├─ Chamber websites (camaradesantiago.cl, ccmetro.cl)
├─ Access member directories
├─ Pre-qualified leads (chamber members = legitimate)
└─ Time: 45-60 mins = 30-50 leads

Mercado Público:
├─ Government supplier registry (mercadopublico.cl)
├─ Filter by small business size
├─ Verify legitimacy + tax compliance
└─ Time: 45-60 mins = 20-40 leads
```

---

## Scoring Rubric (Detailed)

### **Lead Scoring Algorithm**

```
GATE CHECKS (Disqualifying if failed):
├─ Location in target region? YES → Continue
├─ 1-10 employees? YES → Continue
├─ Active business (recent activity)? YES → Continue
└─ If any NO → DISQUALIFY (score = 0)

SCORING (Points out of 100):

Base Score: 50 pts (qualifies minimum threshold)

DIGITAL PRESENCE (+45 pts max):
├─ Active social media (Instagram/Facebook, posts <30 days): +20 pts
├─ Website or online storefront: +15 pts
├─ Business WhatsApp verified: +10 pts

ENGAGEMENT & SIGNALS (+30 pts max):
├─ Clear pain point signals in reviews/posts: +15 pts
├─ Multiple contact channels available: +10 pts
├─ Owner/founder info accessible: +5 pts

GEOGRAPHIC/OPERATIONAL (+25 pts max):
├─ Preferred neighborhood/high-traffic area: +10 pts
├─ Estimated 5+ employees (larger operational base): +8 pts
├─ Years in business (2+ years = stability): +7 pts

EXAMPLE CALCULATIONS:

Example 1: Barbershop, Instagram active, WhatsApp, reviews mention "hard to book"
├─ Base: 50
├─ Instagram active: +20
├─ WhatsApp: +10
├─ Pain point signal: +15
├─ Multiple channels: +10
└─ TOTAL: 105 → Capped at 100 (HOT LEAD)

Example 2: Mini-market, no website, Facebook inactive 6 months
├─ Base: 50
├─ No digital presence: 0
├─ Multiple channels: +8 (phone only)
└─ TOTAL: 58 (WARM LEAD - worth trying)

Example 3: Accounting firm, outdated website, no social, hard to contact
├─ Base: 50
├─ Outdated website: +5
├─ No clear contact: 0
└─ TOTAL: 55 (WARM LEAD - professional service industry valuable)
```

### **Action by Score Tier**

| Score | Tier | Action |
|-------|------|--------|
| **80-100** | 🔥 HOT | Immediate WhatsApp/call (next 24-48 hrs) |
| **60-79** | 🟡 WARM | Email + WhatsApp (this week) |
| **40-59** | 🟠 COOL | Email campaign (batch send) |
| **<40** | ❌ COLD | Archive or manual review (possible false negatives) |

---

## Output Formats

### **CSV Export Template**

```csv
lead_id,business_name,industry,contact_person,phone,email,city,neighborhood,website,facebook_url,instagram_handle,linkedin_url,employee_estimate,operating_since,google_rating,review_count,posting_frequency,whatsapp_enabled,pain_point_primary,pain_point_secondary,tech_readiness_score,lead_score,lead_tier,source,date_found,contact_method,follow_up_date,outreach_status,notes
001,Barbería Los Condes,Barbershop,Juan García,+56987654321,juan@barberia.cl,Santiago,Las Condes,barberia-loscones.cl,facebook.com/barberia.loscones,@barberia_loscones,,2-5,2018,4.7,45,Weekly,Yes,Scheduling,Online presence,High,95,HOT,Google Maps,2025-05-13,WhatsApp,2025-05-14,Contacted,Active on Instagram
```

### **JSON Export Template**

```json
{
  "leads": [
    {
      "lead_id": "001",
      "business": {
        "name": "Barbería Los Condes",
        "industry": "Barbershop",
        "location": {
          "city": "Santiago",
          "neighborhood": "Las Condes",
          "address": "Av. Las Condes 4500, Santiago"
        },
        "size": {
          "employee_estimate": "2-5",
          "operating_since": 2018
        }
      },
      "contact": {
        "person": "Juan García",
        "phone": "+56987654321",
        "email": "juan@barberia.cl",
        "whatsapp_enabled": true
      },
      "digital_presence": {
        "website": "barberia-loscones.cl",
        "facebook": "facebook.com/barberia.loscones",
        "instagram": "@barberia_loscones",
        "posting_frequency": "Weekly"
      },
      "signals": {
        "google_rating": 4.7,
        "review_count": 45,
        "primary_pain_point": "Scheduling appointments",
        "secondary_pain_point": "Online presence building"
      },
      "scoring": {
        "tech_readiness": "High",
        "lead_score": 95,
        "lead_tier": "HOT",
        "scoring_notes": "Active Instagram, WhatsApp enabled, clear scheduling pain point"
      },
      "tracking": {
        "source": "Google Maps",
        "date_found": "2025-05-13",
        "contact_method": "WhatsApp",
        "follow_up_date": "2025-05-14",
        "outreach_status": "Contacted",
        "notes": "Very responsive, showed interest"
      }
    }
  ]
}
```

---

## Integration with Outreach

After extracting and scoring leads, prepare for outreach:

### **WhatsApp Message Template (Industry-Specific)**

**For Barbershops/Salons:**
```
Hola Juan, 👋

He visto tu Barbería Los Condes en Google Maps. 

Noté que muchos clientes en reviews mencionan "difícil conseguir turno". 

Tengo una solución que ayuda a peluquerías a:
✓ Agendar turnos en línea (clientes reservan 24/7)
✓ Recordatorios automáticos (menos cancelaciones)
✓ Gestionar inventario de productos

¿Te gustaría conocer cómo funciona? Es una llamada de 15 min, sin compromiso.

Saludos,
[Tu nombre]
```

**For Cafés/Retailers:**
```
Hola Juan,

Veo que tu café tiene buena presencia en Instagram (posts regulares). ¡Qué bien!

¿Cómo manejas actualmente:
- Turnos de turno de personal?
- Inventario de insumos?
- Reportes de ventas diarias?

Ayudo a cafés pequeños a automatizar estas cosas. Resultado: menos estrés administrativo, más tiempo vendiendo.

¿Charlamos 15 min?

Saludos,
[Tu nombre]
```

### **Email Campaign Subject Lines**

- "Agenda automática para [Nombre Negocio]"
- "[Nombre], simplifica tu [problema específico]"
- "Les ayudé a 20 [tipo negocio] a ahorrar 5 horas/semana"
- "Turno ágil para tu negocio ✓"

---

## Troubleshooting & Tips

### **Common Issues**

**"I found a lead but missing email/website"**
→ Use Hunter.io (free tier) to find email by business name/phone, or manually check their Facebook "About" section

**"Lead has no social media presence but looks legitimate"**
→ Still worth contacting (phone/email). Score may be 50-60, but microenterprises in traditional industries often have low digital presence. Test your messaging.

**"Too many leads, don't know where to start"**
→ Sort by lead_score (HOT first), segment by industry, focus on one neighborhood/industry per day.

**"How do I verify if a business is still active?"**
→ Check Google Maps (updated listing), recent Facebook/Instagram posts (last 30 days), or call to confirm.

**"Should I include family-run businesses?"**
→ YES. Many Chilean micro-businesses are family-run and are perfect fit (owner = decision maker, quick cycles).

### **Best Practices**

- ✅ Start with Google Maps + Facebook (2-3 hours) = 50-100 leads to test messaging
- ✅ Use WhatsApp over email for initial contact (85% adoption in Chile)
- ✅ Extract pain points from Google reviews/Facebook comments = personalization goldmine
- ✅ Focus on one neighborhood/industry first, then expand
- ✅ Re-check social media activity monthly (engagement signal can change)
- ✅ Keep a "follow-up" column to track response rates by industry/channel

---

## Scripts & Tools (if Using Automation)

This skill includes optional Python scripts for batch processing:

- **lead_extractor.py** - Validate and deduplicate raw lead lists
- **lead_scorer.py** - Apply scoring rubric to leads
- **csv_exporter.py** - Export in various formats
- **validation.py** - Check phone formats, email validity, duplicates

To use: `python scripts/lead_scorer.py --input leads.csv --output leads_scored.csv`

---

## References

- `lead_definition.md` - Deep dive on target profile + budget capacity
- `search_tactics.md` - Detailed channel guides (Google Maps, Facebook, Instagram, directories)
- `industry_filters.md` - Full inclusion/exclusion criteria matrix
- `outreach_templates.md` - Pitch frameworks by industry

---

## Next Steps After Extraction

1. **Score & Segment** (this skill) → Organize by score tier + industry
2. **Test Messaging** → Send 20-30 leads WhatsApp/email with A/B variants
3. **Measure Response** → Track response rate by channel, industry, message version
4. **Iterate & Scale** → Double down on winning combinations, expand geographically

---

## Summary

| Question | Answer |
|----------|--------|
| **Who to target?** | Micro-businesses (1-10 employees), service/retail/food sectors, Chile focus |
| **Where to search?** | Google Maps, Facebook, Instagram, PáginsAmarillas, Cámaras de Comercio |
| **What to collect?** | Name, phone, email, industry, website, social profiles, pain points |
| **How to score?** | 0-100 rubric based on digital presence, engagement, pain signals |
| **What to do next?** | Export CSV/JSON, segment by score, test outreach on hot leads |
| **Time to 100 leads?** | 4-5 hours manual research → ~100 leads |
| **Time to 1000 leads?** | 2-3 weeks manual + optional automation tools (Bright Data, Apify) |

