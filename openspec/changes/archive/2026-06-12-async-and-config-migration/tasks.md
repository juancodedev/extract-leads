# Tasks: Async and Config Migration

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~315 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | D1 (config) → D2 (async) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| D1 | Config migration (config.yaml + per-module reads) | PR #1 → main | No interface changes, safe standalone |
| D2 | Async aiohttp (async conversion + pipeline/cli) | PR #2 → main | Depends on D1; all public sigs change sync→async |

## D1: Config Migration (must go first)

- [ ] 1.1 **config.yaml** — Add `extraction`, `enrichment`, `scoring.thresholds`, `scoring.goal_bonuses`, `scoring.dup_threshold` sections (~+25 lines)
- [ ] 1.2 **config_loader.py** — Add `_merge_with_defaults()` deep-merge + unknown-key warning, call from `load_config()` (~+35 lines)
- [ ] 1.3 **extractor.py** — Read `extraction.*` from config in `__init__`, fallback to module constants (~+10 lines, constants stay as defaults)
- [ ] 1.4 **enricher.py** — Read `enrichment.*` from config in `__init__`, fallback to module constants (~+8 lines)
- [ ] 1.5 **analyzer.py** — Read `scoring.thresholds.*` from config in `__init__`, fallback to module constants (~+8 lines)
- [ ] 1.6 **lead_scorer.py** — Read `scoring.goal_bonuses.*` from config (already receives config, just add new dict reads) (~+12 lines)
- [ ] 1.7 **pipeline.py** — Read `scoring.dup_threshold` from config; pass `config` to `PlacesExtractor`, `Enricher`, `WebsiteAnalyzer` constructors (~+8 lines)

## D2: Async aiohttp (depends on D1)

- [x] 2.1 **requirements.txt** — Add `aiohttp>=3.9.0` (~+1 line)
- [x] 2.2 **extractor.py** — `requests` → `aiohttp`; `_request()`, `_get_place_details()`, `search_businesses()` → async; add `session` param + `Semaphore(5)`; `time.sleep()` → `asyncio.sleep()` (~+45 lines)
- [x] 2.3 **enricher.py** — `requests` → `aiohttp`; `find_email()`, `scan_website()` → async; add `session` param + `Semaphore(3)` (~+35 lines)
- [x] 2.4 **analyzer.py** — `requests.Session` → injected `aiohttp.ClientSession`; `analyze()` → async; add `Semaphore(10)`; `generate_audit_report()` stays sync but awaits async `analyze()` (~+35 lines)
- [x] 2.5 **pipeline.py** — `run_pipeline()` → async; create `ClientSession` via `async with`; inject into constructors; use `asyncio.gather(return_exceptions=True)` for parallel enrichment + audits (~+35 lines)
- [x] 2.6 **cli.py** — `main()` → `async def`; wrap entry point with `asyncio.run()`; `run_interactive()` → async (~+15 lines)
