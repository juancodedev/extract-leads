# Proposal: fix-critical-issues

## Intent

Eliminate accumulated technical debt — orphaned dead code, duplicated booking domain definitions, hardcoded industry/city lists, and a monolithic pipeline.py — to reduce maintenance friction and latent bugs before any feature work begins.

## Scope

### In Scope

1. **Delete `files/lead_scorer.py`** — 324 lines, zero imports/references, verified orphaned
2. **Create shared `booking_data` module** — single source of truth for booking domains + skip terms. Fix enricher.py ↔ analyzer.py divergence (2 unique entries each, skip sets differ by 4 terms). Fix the `bookingsystem` partial-substring false-positive bug
3. **Consolidate industry/city data** — remove `AVAILABLE_INDUSTRIES` (49-110) and `ALL_CITIES` (112-138) from pipeline.py; read from config.yaml instead. `run_interactive()` needs fallback defaults for first-run (no config.yaml yet) scenario
4. **Split pipeline.py monolith** (~940/1000 lines) into: `cli.py`, `exporters.py`, `reporters.py`, `config_loader.py`; pipeline.py retains only `run_pipeline()`

### Out of Scope

- Adding tests (Claude Code skill, not a traditional app)
- Async/await migration
- Scoring logic changes
- HTML template restructuring beyond module-split needs

## Capabilities

### New Capabilities

None — pure refactor, no new spec-level behavior introduced.

### Modified Capabilities

None — no requirements change at the spec level.

## Approach

1. **Dead code removal**: `git rm files/lead_scorer.py` — already confirmed zero references via grep across all `.py` files
2. **Booking data module**: Create `booking_data.py` with authoritative `BOOKING_DOMAINS` dict + `BOOKING_SKIP` set. Union of both files' entries. Drop `bookingsystem` (generic term, causes false-positive substring matches). Skip set = union of both (14 terms). Both enricher.py and analyzer.py import from this module instead of defining locally
3. **Industry/city consolidation**: `config_loader.py` provides `load_config()` + `get_default_config()` (hardcoded defaults matching current constants). `run_interactive()` calls `get_default_config()` always (never reads config.yaml). No circular dependency
4. **Pipeline split**: Extract modules, wrap as package with `__init__.py` re-exporting all public symbols for backward compat. `pipeline.py` keeps only `run_pipeline()`. Use relative imports: `from .config_loader import load_config`

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `files/lead_scorer.py` | Removed | Orphaned dead code |
| `enricher.py` | Modified | Import booking_data instead of local booking_domains |
| `analyzer.py` | Modified | Import booking_data instead of local BOOKING_DOMAINS/SKIP |
| `pipeline.py` | Modified | ~940 lines extracted; retains only run_pipeline() |
| `booking_data.py` | New | Shared booking domains dict + skip terms set |
| `config_loader.py` | New | load_config() + get_default_config() fallback |
| `cli.py` | New | argparse + main() dispatch + run_interactive() |
| `exporters.py` | New | export_csv() + load_leads_from_csv() |
| `reporters.py` | New | print_summary() + export_html() |
| `__init__.py` | New | Re-exports for backward compat |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Pipeline split breaks import chain | Med | `__init__.py` re-exports all public symbols; run all CLI flags post-split to verify |
| Interactive mode loses first-run UX | Low | `get_default_config()` provides identical fallback; tests via fresh clone |
| Circular: interactive writes config.yaml it needs | Low | Interactive never reads config.yaml; always uses `get_default_config()` |

## Rollback Plan

Per-file: `git checkout HEAD -- <file>`. Full rollback: `git revert <commit>`. Each task is independently revertible.

## Dependencies

None — pure Python stdlib refactoring.

## Success Criteria

- [ ] `files/lead_scorer.py` deleted; `git grep LeadScorer` only hits active `lead_scorer.py`
- [ ] `booking_data.py` contains union of both domain lists + skip sets; no `bookingsystem` string
- [ ] `python pipeline.py --interactive` works on a fresh clone without config.yaml
- [ ] `python pipeline.py --config config.yaml --limit 5` produces identical output vs main branch
- [ ] `python pipeline.py --from-csv leads.csv --html report.html` works
- [ ] `python pipeline.py --audit report.html --from-csv leads.csv` works
- [ ] All CLI flags (`--seo`, `--ads`, `--ig-web`, `--goal`, `--output`, `--google-key`, `--hunter-key`) produce identical behavior
