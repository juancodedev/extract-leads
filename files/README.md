# Chile Lead Extractor Skill - Complete Guide

**Author:** juancode  
**Version:** 1.0  
**Last Updated:** May 13, 2025

---

## 📋 What's Included

This skill package contains everything you need to find, qualify, and structure high-quality leads from Chilean micro-businesses.

### Files Overview

```
chile-lead-extractor/
├── SKILL.md                          ← Main skill documentation
├── lead_scorer.py                    ← Python script for lead scoring
├── lead_template.csv                 ← CSV template to import leads
├── search_tactics_reference.md       ← Channel-specific search guides
├── industry_filters_reference.md     ← Inclusion/exclusion criteria
├── outreach_templates.md             ← WhatsApp/Email message templates
└── README.md                         ← This file
```

---

## 🚀 Quick Start (Today)

### Option 1: Manual Research (No Tools Needed)

**Time: 4-5 hours → 100+ leads**

```bash
# Step 1: Create your lead template (copy lead_template.csv)
# → Open in Google Sheets or Excel

# Step 2: Search manually (use search_tactics_reference.md)
Day 1 (2 hours):
  ├─ Google Maps: Search 3 industries + extract 30-50 leads
  └─ Add to your spreadsheet

Day 2 (1.5 hours):
  ├─ Facebook: Search + extract 20-30 leads
  └─ Add to spreadsheet

Day 3 (1 hour):
  ├─ Instagram: Search + extract 15-25 leads
  └─ Add to spreadsheet

Day 4 (30 mins):
  ├─ PáginsAmarillas.cl: Directory search
  └─ Add 30-50 more leads

RESULT: 95-155 leads in 4.5 hours
```

### Option 2: With Python Automation (More Structured)

**Time: 1 hour setup + 3 hours research → 100+ scored leads**

```bash
# Step 1: Prepare raw leads CSV
cp lead_template.csv my_leads.csv
# → Fill in manually or import from sources

# Step 2: Run scoring script
python lead_scorer.py my_leads.csv \
  --output-csv my_leads_scored.csv \
  --output-json my_leads_scored.json

# Step 3: Review results
# → Open CSV in spreadsheet
# → Sort by lead_score (highest first)
# → Review scoring summary

RESULT: 100+ leads ranked by quality
```

---

## 📊 Understanding the Scoring System

### Lead Tiers (What They Mean)

| Score | Tier | Action | Timeline |
|-------|------|--------|----------|
| 80-100 | 🔥 HOT | Immediate WhatsApp or phone | Next 24-48 hours |
| 60-79 | 🟡 WARM | Email + WhatsApp this week | This week |
| 40-59 | 🟠 COOL | Batch email campaign | Batch send |
| <40 | ❌ COLD | Archive or manual review | Move to nurture |

### How Scoring Works

Every lead starts at **50 points** (baseline).

Then we add points based on:

```
DIGITAL PRESENCE (+45 max):
├─ Active social media (posts <30 days): +20
├─ Website exists: +15
└─ WhatsApp Business enabled: +10

ENGAGEMENT SIGNALS (+30 max):
├─ Clear pain points in reviews/posts: +15
├─ Multiple contact channels (email, phone, social): +10
└─ Owner info accessible: +5

GEOGRAPHIC & OPERATIONAL (+25 max):
├─ Premium location (Las Condes, Providencia, etc): +10
├─ 5+ employees (larger operation): +8
└─ Stable business (2+ years): +7
```

**Example calculation:**
```
Business: Barbershop in Las Condes
├─ Base score: 50
├─ Instagram active (weekly posts): +20
├─ Has WhatsApp Business: +10
├─ Reviews mention "hard to book": +15
├─ Phone + Email + Instagram: +10
├─ Owner name visible: +5
└─ TOTAL: 110 → Capped at 100 = 🔥 HOT LEAD
```

---

## 🎯 Which Channel to Use? (Decision Tree)

```
Do you have leads already?
├─ NO:
│  └─ Go to RESEARCH PHASE below
│
├─ YES, raw list (names + phones only):
│  └─ Go to BATCH PROCESSING below
│
└─ YES, partially enriched (some websites/social):
   └─ Go to SCORING PHASE below
```

### RESEARCH PHASE: Finding Leads

**Best channels (ranked):**

1. **Google Maps** (Fastest) - 15 min/search = 15-20 leads
   - Use: All industries
   - Extract: Name, phone, website, address, reviews
   - Tip: Read reviews for pain point signals

2. **Facebook** (High quality) - 20 min/search = 20-30 leads
   - Use: Barbershops, cafés, retail, services
   - Extract: Business page URL, contact info in bio, engagement
   - Tip: Check "About" section for hours + contact

3. **Instagram** (Visual + engagement) - 15 min/search = 15-25 leads
   - Use: Salons, cafés, fitness, photography
   - Extract: Handle, bio links (email/WhatsApp), follower count
   - Tip: DM is option if website/email not listed

4. **PáginsAmarillas.cl** (Curated) - 45 min/search = 50+ leads
   - Use: Any industry (filtered by category)
   - Extract: Name, phone, address, category
   - Tip: Easier than manual Google Maps searching

5. **Cámaras de Comercio** (High quality) - 1 hour = 30-50 leads
   - Use: Professional services, verified businesses
   - Extract: Registered business info (highly reliable)
   - Tip: Chamber members = pre-qualified

**Recommendation for Week 1:**
- Day 1-2: Google Maps (fast volume)
- Day 3: Facebook (higher quality)
- Day 4: PáginsAmarillas (fill gaps)
- **Total: 4-5 hours = 100+ leads**

### BATCH PROCESSING: Cleaning Data

If you already have leads but need to clean/structure them:

```bash
# Prepare your CSV (use lead_template.csv as format guide)
# Columns needed:
#  - business_name
#  - industry
#  - phone (ideally)
#  - email (optional)
#  - website (optional)
#  - any other fields from template

# Run Python script to validate:
python lead_scorer.py your_leads.csv \
  --output-csv your_leads_scored.csv

# What it does:
# ✓ Deduplicates (removes duplicates)
# ✓ Validates format (phone, email)
# ✓ Applies scoring rubric
# ✓ Categorizes by lead_tier
```

### SCORING PHASE: Ranking Leads

Once you have enriched lead data (name, contact, website, social):

```bash
python lead_scorer.py my_leads_enriched.csv \
  --output-csv my_leads_scored.csv \
  --output-json my_leads_scored.json

# Outputs:
# 1. CSV with all fields + lead_score + lead_tier
# 2. JSON (API-ready format)
# 3. Summary stats (by tier, by industry)
```

---

## 📝 Data Fields Explained

### Essential Fields (Always Collect)

| Field | Example | Why Matters |
|-------|---------|------------|
| `business_name` | Barbería Los Condes | Verification |
| `industry` | Barbershop | Fit assessment |
| `contact_person` | Juan García | Personalization |
| `phone` | +56987654321 | Primary contact |
| `city` | Santiago | Geographic targeting |
| `source` | Google Maps | Track effectiveness |

### Important Fields (Try to Get)

| Field | Example | Why Matters |
|-------|---------|------------|
| `email` | juan@barberia.cl | Formal follow-up |
| `website` | barberia-loscones.cl | Tech-readiness signal |
| `facebook_url` | facebook.com/barberia | Engagement channel |
| `instagram_handle` | @barberia_loscones | Social presence |
| `posting_frequency` | Weekly | Activity signal |

### Nice-to-Have Fields (Enrichment)

| Field | Example | Why Matters |
|-------|---------|------------|
| `google_rating` | 4.7 stars (45 reviews) | Credibility |
| `employee_estimate` | 2-5 | Operational size |
| `pain_point_primary` | Scheduling | Pitch angle |
| `operating_since` | 2018 | Stability |

---

## 🔍 Common Search Queries (Copy & Paste)

### For Google Maps

```
Barbershops:
  "barbershop Santiago"
  "peluqueria Santiago"
  "barbershop Las Condes"

Cafés:
  "cafe Santiago"
  "coffee shop Las Condes"
  "cafe Providencia"

Retail:
  "minimarket Santiago"
  "ferreteria Santiago"

Professional:
  "contador Santiago"
  "abogado Santiago"
  "consultor Santiago"
```

### For Facebook

```
Search bar:
  "barbershop Santiago Chile"
  "peluqueria Las Condes"

Hashtags:
  #peluqueriasantiago
  #barberíachile
  #cafésantiago
  #ferreteriasantiago
```

### For Instagram

```
Hashtags:
  #peluqueriachile
  #barbershopsantiago
  #cafésantiago
  #salonbellezasantiago

Geolocation:
  Search location → "Santiago"
  Then browse businesses by hashtag
```

### For PáginsAmarillas.cl

```
Just go to: www.paginasamarillas.cl

Categories to search:
  - Peluquerías
  - Barbershops
  - Cafeterías
  - Ferreterías
  - Salones de belleza
  - Servicios de limpieza
```

---

## 📞 Outreach (Next Steps)

Once you have scored leads, refer to **outreach_templates.md** for:

- **WhatsApp messages** (personalized by industry)
- **Email templates** (formal + casual variants)
- **Follow-up sequences** (Day 1, 3, 5, 7...)
- **A/B testing** (compare message variants)

**Quick reference:**
- HOT leads (80+): WhatsApp first, email 2nd
- WARM leads (60-79): Email first, WhatsApp 2nd
- COOL leads (40-59): Batch email (less personalized)

---

## 🎓 Industry-Specific Tips

Refer to **industry_filters_reference.md** for:

- **What to look for** in each industry
- **Inclusion/Exclusion criteria**
- **Industry propensity to buy** (which respond fastest?)
- **Specific pain points** by industry type

**Top 3 highest-response industries (Chile):**
1. Barbershops/Salons (scheduling pain = obvious)
2. Cafés (young owners, social media native)
3. Professional Services (clear ROI on automation)

---

## 📈 Typical Conversion Metrics

Based on research into Chilean SME prospecting:

```
OUTREACH METRICS (Typical):

Cold List → WhatsApp Contact:
├─ Response rate: 20-30%
├─ "Interested" rate: 5-15% (of responses)
└─ Call booked rate: 2-5% (of outreach)

Cold List → Email Contact:
├─ Open rate: 15-25%
├─ Response rate: 5-10%
└─ Call booked rate: 1-3%

GOAL (Week 1):
├─ 100 outreach attempts
├─ 25-30 responses
├─ 3-5 calls booked
└─ 1-2 customers (if offering strong fit)

SCALING (Week 2+):
├─ Find winning message variation
├─ Double down on best-performing channel
├─ Expand geographically or by industry
└─ Measure CAC (cost per acquisition)
```

---

## 🛠 Troubleshooting

### "I'm finding leads but emails are hard to get"

**Solution:** Use Hunter.io (free tier = 50 lookups/month)
- Go to: hunter.io
- Enter business name + website
- Get email address

Or manually check website "Contact" page.

### "How do I verify a lead is still active?"

**Checklist:**
- [ ] Google Maps listing updated (not "Temporarily Closed")
- [ ] Facebook/Instagram has posts in last 30 days
- [ ] Phone number answers (or voicemail sounds current)
- [ ] Website not "Coming Soon" or "Closed"

### "Found 100 leads but overwhelmed"

**Solution:** Prioritize by score
1. Sort by lead_score (descending)
2. Focus first 2 weeks on 80+ (HOT)
3. Once you understand winning message, expand to 60+

### "Getting no responses"

**Common reasons:**
1. Message not personalized (copy-paste signal = ignored)
2. Reaching wrong person (need owner, not employee)
3. Wrong time of day (send 9am-5pm Mon-Fri)
4. Wrong channel (try different channel if no response in 3 days)
5. Pain point not matching their actual pain

**Fix:** Re-read their Google reviews/social posts → personalize message better

### "WhatsApp number invalid"

**Solutions:**
- Use Google Maps to verify current phone
- Try calling first (confirm it's real)
- Use email as fallback
- Move to "follow up later" (numbers change, might be wrong)

---

## 📊 Tracking Your Progress

**Create a tracker spreadsheet:**

```
Week 1:
├─ Leads found: [#]
├─ Leads scored: [#]
├─ HOT leads: [#] (score 80+)
└─ Outreach attempts: [#]

Week 2:
├─ Responses: [#] (%)
├─ "Interested": [#] (%)
├─ Calls booked: [#]
└─ Calls completed: [#]

Metrics to track:
├─ Response rate by channel (WhatsApp vs Email?)
├─ Response rate by industry (which responds fastest?)
├─ Response rate by message variant (A vs B?)
└─ CAC (Cost per customer if paid for leads)
```

---

## 🔄 Weekly Workflow (Recommended)

```
WEEK 1: Research + Scoring
Monday-Wednesday (4 hours):
├─ Google Maps research → 50+ leads
├─ Facebook research → 25+ leads
└─ Add to spreadsheet

Thursday (2 hours):
├─ Directory mining (PáginsAmarillas)
├─ Add 30-50 more leads

Friday (2 hours):
├─ Run Python script to score leads
├─ Review top 30 (HOT leads)
└─ Prepare outreach messages

WEEK 2: Outreach + Refinement
Monday-Wednesday:
├─ Send WhatsApp to 30 HOT leads
├─ Monitor responses
├─ Reply to interested immediately

Thursday-Friday:
├─ Follow up on non-responders (email)
├─ Book any available calls
├─ Analyze what worked (message, channel, industry)

WEEK 3+: Scale + Expand
├─ If working: Double outreach volume
├─ Test new industries or neighborhoods
├─ Refine messaging based on learnings
└─ Start thinking about automation (if doing 1000s)
```

---

## 🚀 Expansion Roadmap

### Phase 1 (Current): Santiago Metropolitan
- **Target:** 500-1000 qualified leads
- **Timeline:** 4-8 weeks
- **Focus:** Validate messaging + landing strategy
- **Channels:** Manual + Semi-automated (Google, Facebook, directories)

### Phase 2 (3-6 months): Other Chilean Regions
- **Expand to:** Valparaíso, Biobío, Los Ríos
- **Leverage:** Proven messaging from Phase 1
- **Automation:** Introduce tools (Apify, Bright Data) for scale
- **Target:** 2000+ leads

### Phase 3 (6-12 months): LATAM Expansion
- **Expand to:** Peru, Colombia, Mexico
- **Adapt:** Local messaging (Spanish variations)
- **Localize:** Region-specific industries + pain points
- **Target:** 5000+ leads

---

## 📚 Reference Documents

This package includes detailed guides:

1. **SKILL.md** - Complete skill documentation
2. **search_tactics_reference.md** - Channel-by-channel guides
3. **industry_filters_reference.md** - Inclusion/exclusion criteria
4. **outreach_templates.md** - Message templates + sequences

**When to use each:**
- Planning research? → search_tactics_reference.md
- Unsure about industry fit? → industry_filters_reference.md
- Ready to reach out? → outreach_templates.md
- General guidance? → SKILL.md

---

## 📧 Support & Questions

If you have questions about:
- **Scoring logic** → See SKILL.md "Scoring Rubric" section
- **Channel tactics** → See search_tactics_reference.md
- **Industry suitability** → See industry_filters_reference.md
- **Message templates** → See outreach_templates.md

---

## 📄 License & Attribution

This skill was created for lead generation in the Chilean SME market.

Feel free to:
- ✅ Modify templates for your business
- ✅ Adapt scoring rubric for different markets
- ✅ Add new industries to filters
- ✅ Share with team

---

## 🎯 Success Criteria (Week 1)

By end of Week 1, you should have:

- ✅ 100+ leads in structured CSV
- ✅ Leads scored and ranked by quality
- ✅ Top 30 HOT leads identified
- ✅ Outreach message drafted
- ✅ First 10-20 leads contacted

**If achieved:** Ready for Week 2 outreach + scaling!

---

**Version 1.0 | Created May 2025 | For Chilean Market SME Prospecting**
