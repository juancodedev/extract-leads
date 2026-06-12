# Design: Optimize Code Quality

## Technical Approach

Four independent refactoring deliverables — no behavioral changes, no new capabilities. Each deliverable is a self-contained commit.

1. **Templates**: Extract inline HTML from `reporters.py` and `analyzer.py` into Jinja2 templates with a shared base shell
2. **Constants**: Replace bare numeric literals across 4 files with named module-level constants
3. **Cleanup**: Delete duplicate docs from `files/`, move reference files to `docs/`
4. **Dedup**: Add `rapidfuzz`-based fuzzy dedup to `pipeline.py` with token_sort_ratio at threshold 85

## Architecture Decisions

### Decision: Jinja2 over string templates

| Option | Tradeoff | Decision |
|--------|----------|----------|
| F-string HTML (current) | Unmaintainable, no separation of concerns | ❌ Reject |
| Jinja2 `Environment` + `FileSystemLoader` | Clear MVC split, partials via `extends`, 1 new dep (MIT) | ✅ **Adopt** |
| Mako / Chameleon | Overkill, fewer users in Python ecosystem | ❌ Reject |

`contacts_html` stays as Python string — building per-row contact icons in Jinja2 would require filters or macros that add complexity without benefit.

### Decision: Inline dedup in pipeline.py

| Option | Tradeoff | Decision |
|--------|----------|----------|
| New `dedup.py` module | Cleaner if more dedup features come, but overkill for < 30 lines | ❌ Reject |
| Inline function + call in `run_pipeline()` | Co-located with the only call site, no import overhead | ✅ **Adopt** |

### Decision: `rapidfuzz` over `fuzzywuzzy`

`rapidfuzz` is MIT-licensed, actively maintained, 10-100x faster, and has the same API (`token_sort_ratio`). `fuzzywuzzy` is GPL and unmaintained.

## Data Flow

```
D1 (Jinja2):
  reporters.py ──export_html()──→ data dict ──→ lead_report.html → rendered HTML
  analyzer.py  ──_generate_html()→ data dict ──→ audit_report.html → rendered HTML
                              base.html (shared shell via extends)

D4 (Dedup):
  extractor → enricher → scorer ──→ all_leads (scored) ──→ deduplicate(all_leads) ──→ unique leads
                                                                ↑
                                                          sorted by score desc
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `templates/base.html` | Create | Shared HTML shell (DOCTYPE, head, CSS, content+footer blocks) |
| `templates/lead_report.html` | Create | Lead report page, extends base.html |
| `templates/audit_report.html` | Create | Audit report page, extends base.html |
| `reporters.py` | Modify | Replace ~140 lines inline HTML with Jinja2 `env.get_template().render(data)` |
| `analyzer.py` | Modify | Replace ~65 lines inline HTML + extract ~30 magic numbers as constants |
| `lead_scorer.py` | Modify | Extract 6 goal-specific bonus/penalty values as constants |
| `extractor.py` | Modify | Extract 3 literals (`3`, `2`, `15`) as constants |
| `enricher.py` | Modify | Extract 2 literals (`10`, `3`) as constants |
| `pipeline.py` | Modify | Add `deduplicate_leads()` function + call in `run_pipeline()` |
| `requirements.txt` | Modify | Add `Jinja2`, `rapidfuzz` |
| `files/QUICK_START_GUIDE.md` | Delete | Duplicate of root README |
| `files/README.md` | Delete | Duplicate of root README |
| `docs/industry_filters_reference.md` | Create (move) | Moved from `files/` |
| `docs/search_tactics_reference.md` | Create (move) | Moved from `files/` |
| `docs/outreach_templates.md` | Create (move) | Moved from `files/` |
| `docs/lead_template.csv` | Create (move) | Moved from `files/` |

## Interfaces / Contracts

### D1 — Jinja2 data contract for `lead_report.html`

```python
{
    "total": int,
    "phones": int,
    "websites": int,
    "with_wa": int,
    "with_booking": int,
    "avg_rating": float,
    "now": str,
    "tiers": [{"name": str, "count": int, "pct": int, "color": str}],
    "industries": [{"name": str, "count": int, "pct": int}],
    "rows": [{"num": int, "name": str, "industry": str, "city": str,
              "contacts_html": str, "booking_badge": str, "rating": str,
              "reviews": str, "tier": str, "tier_color": str, "tier_bg": str,
              "score": int}],
    "top_opportunities": [{"name": str, "industry": str, "city": str,
                           "score": int, "notes": str, "audit_badges": str,
                           "tier": str, "tier_color": str, "tier_bg": str,
                           "suggested_msg": str}],
}
```

### D1 — Jinja2 data contract for `audit_report.html`

```python
{
    "audited": int,
    "total_leads": int,
    "now": str,
    "ok_sites": int,
    "error_sites": int,
    "avg_rt": int,
    "with_booking": int,
    "with_whatsapp": int,
    "cards": [...],  # per-site analysis dicts
}
```

### D2 — Module constants

| File | Constants |
|------|-----------|
| `extractor.py` | `MAX_PAGES=3`, `PAGE_TOKEN_DELAY=2`, `REQUEST_TIMEOUT=15` |
| `enricher.py` | `HUNTER_TIMEOUT=10`, `WEBSITE_SCAN_TIMEOUT=10`, `MIN_HANDLE_LENGTH=3` |
| `lead_scorer.py` | `WEB_NO_SITE_BONUS=40`, `WEB_HAS_SITE_PENALTY=-10`, `SEO_NO_SOCIAL_BONUS=20`, `SEO_POOR_TECH_BONUS=30`, `SEO_NO_SITE_PENALTY=-20`, `ADS_HAS_SITE_BONUS=20`, `ADS_LOW_RATING_BONUS=15`, `ADS_LOW_RATING_THRESHOLD=4.2`, `GENERAL_HIGH_RATING_THRESHOLD=4.5` |
| `analyzer.py` | `TITLE_TRUNCATE=100`, `DESC_TRUNCATE=150`, `H1_TRUNCATE=80`, `SLOW_THRESHOLD_MS=3000`, `WARN_THRESHOLD_MS=1500`, `TITLE_MIN=30`, `TITLE_IDEAL_MIN=50`, `TITLE_IDEAL_MAX=70`, `DESC_MIN=80`, `DESC_IDEAL_MIN=120`, `DESC_IDEAL_MAX=170`, `CONTENT_SPARSE=100`, `CONTENT_LOW=300`, `MAX_IMPROVEMENTS=12`, `TECH_BASE_SCORE=50`, `TECH_SCORE_SSL=5`, `TECH_SCORE_FAST=5`, plus per-signal scores through `TECH_SCORE_BOOKING=3`, `TECH_MAX_SCORE=100`, `TECH_GREEN_THRESHOLD=80`, `TECH_YELLOW_THRESHOLD=50` |

### D4 — Dedup function

```python
from rapidfuzz import fuzz

DUP_THRESHOLD = 85

def deduplicate_leads(leads: List[Dict], threshold: int = DUP_THRESHOLD) -> List[Dict]:
    """Fuzzy-deduplicate by business name, keep highest-scored."""
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| D1 | HTML output identical | Run `pipeline.py --from-csv --html` before and after, diff |
| D1 | No inline HTML strings | `grep -n '"""<' reporters.py analyzer.py` returns empty |
| D2 | Constants loadable | `python -c "from analyzer import TITLE_TRUNCATE; print(TITLE_TRUNCATE)"` |
| D2 | No bare literals > 1 | `grep -nE '[^a-zA-Z_][2-9][0-9]?[^a-zA-Z_]'` on modified files (exclude 0, 1) |
| D3 | files/ state | `ls files/` shows only `SKILL.md` + `lead_template.csv` |
| D3 | docs/ state | `ls docs/` shows 4 moved reference files |
| D4 | Dedup logic | `python -c "from pipeline import deduplicate_leads; ..."` with known dupes |

## Migration / Rollout

No migration required. Each deliverable is a standalone commit. Rollback is per-commit `git revert`.

## Implementation Order

No dependencies between deliverables. Recommended order: D2 → D3 → D4 → D1 (D1 last to minimize idle time — requires templates/ dir and Jinja2 install, easy to verify by visual diff).
