# Chile Lead Extractor - Visual Flow & Quick Reference

## 🎯 The Big Picture

```
YOUR GOAL:
  Find Chilean micro-business leads
      ↓
  Qualify them (score by fit)
      ↓
  Export for outreach
      ↓
  Contact + Convert
```

---

## 📊 Quick Decision Matrix

```
┌─────────────────────────────────────────┐
│ WHAT DO YOU NEED TO DO RIGHT NOW?       │
└─────────────────────────────────────────┘

1. FIND LEADS?
   └─ Use: search_tactics_reference.md
   └─ Tools: Google Maps, Facebook, Instagram
   └─ Time: 4-5 hours = 100+ leads

2. CLEAN UP RAW LEAD LIST?
   └─ Use: lead_scorer.py script
   └─ Input: CSV with business names + phones
   └─ Output: Scored + ranked leads

3. WRITE OUTREACH MESSAGES?
   └─ Use: outreach_templates.md
   └─ Variants: WhatsApp, Email, A/B tests
   └─ Personalization: By industry + pain point

4. CHECK IF BUSINESS FITS?
   └─ Use: industry_filters_reference.md
   └─ Criteria: Size (1-10 employees), industry, activity status
   └─ Action: Include or exclude from list

5. UNDERSTAND SCORING SYSTEM?
   └─ Use: SKILL.md → "Scoring Rubric" section
   └─ Tiers: HOT (80+), WARM (60-79), COOL (40-59), COLD (<40)
   └─ Action: Different outreach by tier
```

---

## ⚡ Fastest Path: 100 Leads in 1 Day

```
TIMELINE: 1 Day (4-5 Hours)

TIME    ACTIVITY                 RESULT
────────────────────────────────────────
9:00    Google Maps research     20 leads
        (3 industries x 15 mins)
        
10:30   Break (5 mins)

10:35   Facebook search          25 leads
        (2 industries x 30 mins)

11:35   Break (5 mins)

11:40   Instagram search         20 leads
        (3 hashtags x 15 mins)

12:40   Lunch (1 hour)

1:40    PáginsAmarillas search   50 leads
        (1 hour automated)

2:40    Final cleanup            105 LEADS
        (consolidate + dedupe)   READY

NEXT:
  Day 2-3: Enrich top 50 (websites, social media)
  Day 4: Run scoring script
  Day 5: Start outreach
```

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ RAW RESEARCH (Manual or Automated)                      │
│                                                         │
│ Google Maps → Facebook → Instagram → Directories        │
│ Names, phones, websites, social handles                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ IMPORT INTO SPREADSHEET (CSV Format)                    │
│                                                         │
│ [Template provided: lead_template.csv]                  │
│ Columns: name, phone, email, website, industry, etc.    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ RUN SCORING SCRIPT (Optional but Recommended)           │
│                                                         │
│ python lead_scorer.py input.csv \                       │
│   --output-csv output_scored.csv \                      │
│   --output-json output_scored.json                      │
│                                                         │
│ Output:                                                 │
│  ✓ Deduplication                                        │
│  ✓ Validation (phone format, email)                    │
│  ✓ Scoring (0-100 points)                             │
│  ✓ Tier assignment (HOT/WARM/COOL/COLD)               │
│  ✓ Summary statistics                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ EXPORT FOR OUTREACH                                     │
│                                                         │
│ CSV: For spreadsheet review + manual outreach           │
│ JSON: For API integration or CRM import                 │
│ WhatsApp List: Formatted phone numbers (+56 9 ...)     │
│ Email List: Validated emails for campaigns             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ OUTREACH CAMPAIGNS                                      │
│                                                         │
│ HOT Leads (80+):        WhatsApp → Email → Phone       │
│ WARM Leads (60-79):     Email → WhatsApp → Phone       │
│ COOL Leads (40-59):     Batch Email → Nurture List     │
│ COLD Leads (<40):       Manual review or Archive        │
│                                                         │
│ [Use templates from: outreach_templates.md]            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ TRACKING & OPTIMIZATION                                 │
│                                                         │
│ Response rates by:                                      │
│  - Channel (WhatsApp vs Email)                         │
│  - Industry (Barbershop vs Café vs Services)           │
│  - Message variant (A vs B)                            │
│  - Lead tier (HOT vs WARM vs COOL)                     │
│                                                         │
│ → Iterate messaging + focus on winning combination     │
└─────────────────────────────────────────────────────────┘
```

---

## 📱 Channel Comparison (At a Glance)

```
CHANNEL    SPEED   QUALITY  VOLUME  SETUP   BEST FOR
────────────────────────────────────────────────────
Maps       ⚡⚡⚡    ⭐⭐⭐   ~20/hr  None    Quick start
Facebook   ⚡⚡     ⭐⭐⭐   ~25/hr  None    High engagement
Instagram  ⚡⚡     ⭐⭐⭐   ~20/hr  None    Visual businesses
PágAmarillas ⚡    ⭐⭐⭐  ~50/hr  1 min   Volume
Chambers   ⚡      ⭐⭐⭐⭐  ~30/hr  5 min   Quality/verified
Mercado Púb ⚡     ⭐⭐⭐⭐  ~20/hr  5 min   Government registry

RECOMMENDATION: Mix Google + Facebook + Directories
               = Best speed/quality/effort balance
```

---

## 🎯 Lead Scoring Cheat Sheet

```
EVERY LEAD STARTS AT: 50 POINTS

ADD POINTS FOR:
├─ Active social media (posts <30 days)      → +20 pts
├─ Website or online presence                → +15 pts
├─ Clear pain point signals                  → +15 pts
├─ Multiple contact channels                 → +10 pts
├─ WhatsApp Business enabled                 → +10 pts
├─ Premium location (Las Condes, etc)        → +10 pts
├─ 5+ employees (operational size)           → +8 pts
├─ Owner info accessible                     → +5 pts
├─ 2+ years operating (stability)            → +7 pts
└─ TOTAL MAX: 100 POINTS

SCORE TIERS & ACTIONS:
├─ 80-100: 🔥 HOT      → Call/WhatsApp ASAP (24-48h)
├─ 60-79:  🟡 WARM     → Email + WhatsApp (this week)
├─ 40-59:  🟠 COOL     → Batch email (next week)
└─ <40:    ❌ COLD     → Archive/nurture (3-6 months)
```

---

## 💬 Outreach Strategy by Tier

```
🔥 HOT LEADS (80-100 points)
├─ Preferred channel: WhatsApp
├─ Timing: Within 24 hours of finding
├─ Message: Highly personalized (mention specific pain point)
├─ Follow-up: If no response → Email (day 3) → Phone (day 5)
└─ Goal: Get on call within 3 days

🟡 WARM LEADS (60-79 points)
├─ Preferred channel: Email (more formal)
├─ Timing: Within 3 days
├─ Message: Personalized but slightly less urgent
├─ Follow-up: If no response → WhatsApp (day 4) → Phone (day 7)
└─ Goal: Get on call within 1 week

🟠 COOL LEADS (40-59 points)
├─ Preferred channel: Email (batch-friendly)
├─ Timing: Batch send (once per week)
├─ Message: Semi-templated (less personalization needed)
├─ Follow-up: General newsletters + content marketing
└─ Goal: Nurture list (3-6 month follow-up)

❌ COLD LEADS (<40 points)
├─ Action: Archive or manual review
├─ When: Monthly check-in (maybe still worth outreach?)
└─ Note: Don't waste time, focus on HOT first
```

---

## 📈 Timeline: Week 1 → Month 1

```
WEEK 1: Research + Setup
├─ Mon-Tue: Find 100 leads
├─ Wed-Thu: Enrich data (websites, social media)
├─ Fri: Score + prioritize
└─ END STATE: 100 leads, top 30 HOT identified

WEEK 2: Outreach Blitz
├─ Mon-Tue: Contact 30 HOT leads (WhatsApp)
├─ Wed-Thu: Follow-up + capture responses
├─ Fri: Book calls + analyze what worked
└─ END STATE: 3-5 calls booked, winning message identified

WEEK 3: Test & Optimize
├─ Mon-Tue: Contact 30 WARM leads (Email + WhatsApp)
├─ Wed: Refine messaging based on Week 2 learnings
├─ Thu-Fri: Follow-ups + more calls
└─ END STATE: 6-8 calls booked, message variations tested

WEEK 4: Scale
├─ Mon-Wed: Expand to new neighborhood/industry with proven message
├─ Thu-Fri: Continue COOL lead outreach + nurture
└─ END STATE: 10+ calls in pipeline, repeatable process

GOAL BY END OF MONTH:
├─ 500+ qualified leads in database
├─ 80+ calls attempted
├─ 10-15 calls completed
├─ 2-5 customers/wins
└─ CAC (Cost Per Acquisition) calculated
```

---

## 🏭 Batch Processing Workflow (If You Have Raw List)

```
INPUT: CSV with ~500 business names + phone numbers

STEP 1: Import Template
└─ Copy lead_template.csv as starting point

STEP 2: Match Your Data
└─ Rename columns to match template
└─ Phone format: +56 9 XXXX XXXX (validate)

STEP 3: Enrich (Optional but Recommended)
├─ Website: Google search "business name"
├─ Email: Use Hunter.io (free tier) or check contact page
├─ Social: Search Facebook/Instagram for business page
├─ Industry: Confirm business type

STEP 4: Run Scoring Script
└─ python lead_scorer.py input.csv \
   └─ --output-csv output_scored.csv

STEP 5: Review Results
├─ Open CSV in spreadsheet
├─ Sort by lead_score (descending)
├─ Review summary stats (included in script output)

STEP 6: Export for Outreach
├─ Filter by lead_tier (start with HOT)
├─ Export phone numbers to WhatsApp list
├─ Export emails to email campaign tool

TIME ESTIMATE: 1-2 hours for 500 leads
```

---

## ✅ Checklist: Ready to Start?

```
BEFORE YOU BEGIN:

TOOLS:
  ☐ Google account (for Maps + Sheets)
  ☐ Facebook account
  ☐ Instagram account (optional but helpful)
  ☐ Python installed (optional, for scoring script)

TEMPLATES DOWNLOADED:
  ☐ lead_template.csv
  ☐ SKILL.md (main reference)
  ☐ search_tactics_reference.md
  ☐ outreach_templates.md

KNOWLEDGE:
  ☐ Understood lead scoring system (0-100 points)
  ☐ Identified 2-3 target industries to research
  ☐ Identified 2-3 neighborhoods in Santiago to start with
  ☐ Have phone + email ready (for outreach)

SETUP (30 mins):
  ☐ Create new Google Sheet → rename "Chile Leads 2025"
  ☐ Copy header row from lead_template.csv
  ☐ Create folder for leads (local or Drive)
  ☐ Bookmark search_tactics_reference.md (quick lookup)

READY TO START:
  ☑️ YES → Go to Google Maps, search your first industry
  ☑️ NO → Review README.md or SKILL.md first
```

---

## 🚀 Day 1 Action Plan

```
9:00 AM:  Open Google Maps
          Search: "barbershop Santiago"
          Extract: Name, phone, website, neighborhood
          Target: 15-20 leads in 20 minutes

9:25 AM:  Search 2nd industry (e.g., "café Las Condes")
          Extract same fields
          Target: 15-20 leads

9:45 AM:  Search 3rd industry (e.g., "salón belleza")
          Target: 15-20 leads

10:05 AM: Open Facebook
          Search: Same 3 industries + hashtags
          Extract: Page URL, contact info in bio
          Target: 20-30 leads in 30 minutes

10:40 AM: Break (15 mins)

10:55 AM: Open Instagram
          Search hashtags + geolocation
          Extract: Handle, bio links (email/WhatsApp)
          Target: 15-25 leads

11:35 AM: Export data to Google Sheet
          Clean up formatting
          Deduplicate (remove if exact same name + phone)

12:00 PM: LUNCH

1:00 PM:  Review what you collected
          Count leads: TARGET is 70-100 by end of day
          Identify gaps (missing emails? websites?)

1:30 PM:  Optional: PáginsAmarillas directory search
          If you want to hit 100+ leads

3:00 PM:  END OF DAY
          If successful: 70-100 leads ready for scoring
          Next day: Enrich + score + prepare for outreach
```

---

## 📊 Success Metrics (Track These)

```
RESEARCH PHASE:
├─ Leads found: ______ (target: 100+)
├─ Leads with phone: ______ (target: 95%+)
├─ Leads with email: ______ (target: 50%+)
├─ Leads with website: ______ (target: 40%+)
└─ Time spent: ______ hours

SCORING PHASE:
├─ Leads scored: ______ (should = total found)
├─ HOT leads (80+): ______ (target: 20-30%)
├─ WARM leads (60-79): ______ (target: 30-40%)
├─ COOL leads (40-59): ______ (target: 20-30%)
└─ Scoring time: ______ minutes

OUTREACH PHASE:
├─ HOT leads contacted: ______ (target: all)
├─ Response rate: ______ % (target: 20-30%)
├─ Interested: ______ (target: 5-10% of responses)
├─ Calls booked: ______ (target: 2-5% of outreach)
└─ Calls completed: ______ (target: 70% booking→completion)

OVERALL:
├─ Lead quality score: ______ / 10 (subjective)
├─ Message fit: ______ / 10 (did pain point match?)
├─ Next action: Continue? Pivot? Scale?
```

---

## 🎓 Learning Resources

```
INCLUDED IN PACKAGE:
├─ SKILL.md .......................... Complete skill guide
├─ search_tactics_reference.md ....... How to find leads
├─ industry_filters_reference.md .... Which businesses to target
├─ outreach_templates.md ............ How to contact leads
├─ README.md ......................... Setup + troubleshooting
├─ lead_scorer.py ................... Python scoring script
└─ lead_template.csv ................ Data template

EXTERNAL RESOURCES:
├─ Hunter.io ........................ Email finder (free tier)
├─ Google Maps ...................... Lead discovery
├─ Facebook Business ................ Lead discovery
├─ PáginsAmarillas.cl ............... Directory (Chile-specific)
└─ Your own observations ............ Pain point research
```

---

## 💡 Pro Tips

```
1. START NARROW, EXPAND LATER
   Week 1: Focus on 1 neighborhood + 1-2 industries
   Week 2: Expand to 2-3 neighborhoods
   Week 3: Add new industries based on learnings

2. PHONES FIRST, EMAILS SECOND
   In Chile: WhatsApp is king (85% adoption)
   Video calls preferred over phone
   Email is backup if WhatsApp fails

3. SOCIAL MEDIA = PERSONALITY TEST
   High engagement = receptive to new ideas
   Low engagement = probably busy or traditional
   No social = harder to reach but not impossible

4. REVIEWS ARE GOLD
   Read Google/Facebook reviews for pain point language
   Look for: "hard to book", "no website", "slow"
   Use these words in your pitch

5. VERIFY BEFORE SCORING
   Call the number (quick verification)
   Check if Facebook page is legitimate
   If business closed = remove from list

6. BATCH IS YOUR FRIEND
   Don't contact 1 lead at a time
   Batch = 10-20 contacts per day
   Easier to measure, optimize

7. PERSONALIZATION > VOLUME
   1 personalized message = 3-5x response vs generic
   Takes 2 extra minutes per lead
   Worth it for HOT leads

8. PAIN POINT = CURRENCY
   Generic pitch = ignored
   Specific pain point = noticed + responded
   Example: "Saw your reviews, many clients mention 
            'hard to book turnos'"
   vs
   "Hi, do you want to grow?"
```

---

**Created: May 13, 2025 | For: Chilean SME Lead Generation**

