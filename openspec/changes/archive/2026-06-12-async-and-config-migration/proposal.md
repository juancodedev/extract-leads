# Proposal: Async and Config Migration

## Intent

Eliminate the two biggest remaining pain points: system tuning requires editing Python source (module constants), and the synchronous `requests` stack limits throughput to ~2-3 leads/minute. Both block scaling to 500+ lead runs.

## Scope

### In Scope
- **Config migration**: ~15 constants → `config.yaml` sections (`extraction`, `enrichment`, `scoring.thresholds`, `scoring.goal_bonuses`), with key validation + fallback to module defaults
- **Async aiohttp migration**: `extractor.py`, `enricher.py`, `analyzer.py` → async; `pipeline.py`, `cli.py` async plumbing; single `aiohttp.ClientSession` per run with per-service semaphores (Places: 5, Hunter: 3, scans: 10)
- **Session management**: Shared `ClientSession` + semaphores, dependency-injected into constructors

### Out of Scope
- Replacing `requests` everywhere (sync callers keep it; internal pipeline uses async)
- pytest-asyncio or test infrastructure
- HTML output changes
- Scoring algorithm changes

## Capabilities

### New Capabilities
None — pure implementation refactor, no new user-facing capability.

### Modified Capabilities
None — CLI flags, output shapes, and error handling surfaces are identical.

## Approach

**Deliverable 1** — Config: Add `extraction:`, `enrichment:`, `scoring.thresholds:`, `scoring.goal_bonuses:` sections to `config.yaml`. Enhance `config_loader.load_config()` with unknown-key warnings and recursive fallback to module defaults. Each module reads its values via a `get(key, default)` helper instead of bare module constants. Keep module constants as defaults.

**Deliverable 2** — Async: Add `aiohttp` dep. Create `shared.ClientSession` factory. Flip each `_request()` / `find_email()` / `scan_website()` / `analyze()` to async. `pipeline.run_pipeline()` becomes async, uses `asyncio.gather(return_exceptions=True)` for parallel enrichment/scans. `cli.main()` becomes `async def` wrapped in `asyncio.run()`. `LeadScorer` stays synchronous.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `config.yaml` | Modified | New sections for thresholds, timeouts, goal bonuses |
| `config_loader.py` | Modified | Key validation, fallback defaults |
| `extractor.py` | Modified | Constants → config; `requests` → `aiohttp` |
| `enricher.py` | Modified | Constants → config; `requests` → `aiohttp` |
| `analyzer.py` | Modified | Constants → config; `requests.Session` → `aiohttp.ClientSession` |
| `lead_scorer.py` | Modified | Constants → config (stays sync) |
| `pipeline.py` | Modified | `run_pipeline()` → async; `DUP_THRESHOLD` → config |
| `cli.py` | Modified | `main()` → `async def` + `asyncio.run()` |
| `requirements.txt` | Modified | +`aiohttp` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Sync→async cascading breakage | Med | Per-module async flip with `asyncio.gather(return_exceptions=True)`; one failure doesn't kill batch |
| Config key typo silently falls back | Low | `load_config()` warns on unknown keys; default fallback prevents crash |

## Rollback Plan

Per-deliverable `git revert`. Config changes are safe to revert independently. Async changes revert as one unit (interface change). Test with `python pipeline.py --limit 5` before and after each revert.

## Dependencies

- `aiohttp` (PyPI, Apache 2.0)

## Success Criteria

- [ ] `python pipeline.py --limit 5` produces identical CSV output (same rows, same fields)
- [ ] `python pipeline.py --from-csv test.csv --html report.html` produces identical HTML
- [ ] All CLI flags (`--goal`, `--seo`, `--ads`, `--ig-web`, `--interactive`) work identically
- [ ] Config file with all keys removed still works (falls back to module defaults)
- [ ] Deleting a single key from any new section triggers a log warning but no crash
- [ ] 100-lead run completes with 0 `requests` imports called (verified via `PYTHONWARNINGS`)
