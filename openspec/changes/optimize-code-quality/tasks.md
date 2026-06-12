# Tasks: Optimize Code Quality

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~550 (adds + deletes) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: D2+D3+D4 (~150 lines) → PR 2: D1 (~400 lines) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Module constants + files cleanup + dedup | PR 1 | Base main; well under 400 lines |
| 2 | Jinja2 templates + wiring | PR 2 | The heavy lift; base main (or PR 1 if stacked) |

## Phase 1: Module-Level Constants (D2)

- [ ] 1.1 `extractor.py` — Add `MAX_PAGES=3`, `PAGE_TOKEN_DELAY=2`, `REQUEST_TIMEOUT=15` at module level; replace bare literals
- [ ] 1.2 `enricher.py` — Add `HUNTER_TIMEOUT=10`, `WEBSITE_SCAN_TIMEOUT=10`, `MIN_HANDLE_LENGTH=3`; replace bare literals
- [ ] 1.3 `lead_scorer.py` — Add `WEB_NO_SITE_BONUS=40`, `WEB_HAS_SITE_PENALTY=-10`, `SEO_NO_SOCIAL_BONUS=20`, `SEO_POOR_TECH_BONUS=30`, `SEO_NO_SITE_PENALTY=-20`, `ADS_HAS_SITE_BONUS=20`, `ADS_LOW_RATING_BONUS=15`, `ADS_LOW_RATING_THRESHOLD=4.2`, `GENERAL_HIGH_RATING_THRESHOLD=4.5`; replace bare literals
- [ ] 1.4 `analyzer.py` — Add ~25 tech scoring constants (`TITLE_TRUNCATE`, `DESC_TRUNCATE`, `SLOW_THRESHOLD_MS`, `WARN_THRESHOLD_MS`, `MAX_IMPROVEMENTS`, `TECH_BASE_SCORE`, per-signal scores, thresholds); replace bare literals
- [ ] 1.5 Verify: `grep -nE '[^a-zA-Z_][2-9][0-9]?[^a-zA-Z_]'` on modified files returns no hits (excluding 0, 1, index lookups)

## Phase 2: Fuzzy Dedup (D4)

- [ ] 2.1 `requirements.txt` — Add `rapidfuzz`
- [ ] 2.2 `pipeline.py` — Add `from rapidfuzz import fuzz`, `DUP_THRESHOLD=85`, `deduplicate_leads()` function with `token_sort_ratio`
- [ ] 2.3 `pipeline.py` — Call `deduplicate_leads(all_leads)` before `return all_leads` in `run_pipeline()`
- [ ] 2.4 Verify: `python -c "from pipeline import deduplicate_leads; assert len(deduplicate_leads([{'name':'Café A','score':90},{'name':'Cafe A','score':85}])) == 1"`

## Phase 3: files/ Cleanup (D3)

- [ ] 3.1 Delete `files/QUICK_START_GUIDE.md` and `files/README.md`
- [ ] 3.2 Create `docs/` directory; `git mv` 4 files: `files/industry_filters_reference.md`, `files/search_tactics_reference.md`, `files/outreach_templates.md`, `files/lead_template.csv`
- [ ] 3.3 Verify: `ls files/` shows only `SKILL.md` + `lead_template.csv`; `ls docs/` shows 4 moved files

## Phase 4: Jinja2 Templates (D1)

- [ ] 4.1 `requirements.txt` — Add `Jinja2`
- [ ] 4.2 Create `templates/base.html` — Shared HTML shell (DOCTYPE, head with CSS, body with content+footer blocks)
- [ ] 4.3 Create `templates/lead_report.html` — Extends base.html; stats grid, ranking legend, top opportunities, table, industry/tier cards
- [ ] 4.4 Create `templates/audit_report.html` — Extends base.html; stats bar, per-site cards with improvements grid
- [ ] 4.5 `reporters.py` — Replace ~140 lines inline HTML with `Environment(FileSystemLoader).get_template('lead_report.html').render(data)`; pass computed data dict
- [ ] 4.6 `analyzer.py` — Replace ~65 lines inline HTML in `_generate_html()` with Jinja2 render
- [ ] 4.7 Verify: `grep -n '"""<' reporters.py analyzer.py` returns empty; run `python pipeline.py --from-csv --html test.html` (no crash)
