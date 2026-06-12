# Tasks: fix-critical-issues

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~2,030 (847 added, 1,183 deleted) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Tasks 1+2) → PR 2 (Tasks 4+5) → PR 3 (Tasks 3+6) → PR 4 (Task 7) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Base | Notes |
|------|------|-----------|------|-------|
| 1 | Orphan deletion + booking data module | PR 1 | main | No pipeline.py changes |
| 2 | Exporters + Reporters modules | PR 2 | main | Remove pure-copy functions from pipeline.py |
| 3 | Config loader + CLI refactor | PR 3 | main | Replace inline constants + move entry point |
| 4 | Final verification | PR 4 | main | Smoke-test all flags & import paths |

## Phase 1: Foundation

- [ ] 1.1 `git rm files/lead_scorer.py` — 324 lines, zero references confirmed
- [ ] 1.2 Create `booking_data.py` — `BOOKING_DOMAINS: Dict[str, str]` (union, exclude `bookingsystem`), `BOOKING_SKIP: Set[str]` (union, 17 terms)
- [ ] 1.3 `enricher.py` — replace inline `booking_domains` (lines 134-142) + `booking_skip` (lines 143-145) with `from booking_data import BOOKING_DOMAINS, BOOKING_SKIP`
- [ ] 1.4 `analyzer.py` — replace inline `BOOKING_DOMAINS` (lines 18-39) + `BOOKING_SKIP` (lines 57-62) with same import

## Phase 2: Exporters + Reporters

- [ ] 2.1 Create `exporters.py` — `export_csv()`, `load_leads_from_csv()` from pipeline.py lines 320-357, 866-877
- [ ] 2.2 Create `reporters.py` — `print_summary()` (lines 359-394), `export_html()` (lines 560-863) including the ~280-line HTML template
- [ ] 2.3 `pipeline.py` — remove `csv`, `html` imports; remove `export_csv`, `load_leads_from_csv`, `print_summary`, `export_html` definitions

## Phase 3: Config Loader + CLI

- [ ] 3.1 Create `config_loader.py` — `load_config()`, `get_default_industries()` (12 entries matching current `AVAILABLE_INDUSTRIES`), `get_default_locations()` (25 entries matching `ALL_CITIES`)
- [ ] 3.2 Create `cli.py` — `main()` (argparse, all 12 flags), `run_interactive()` (calls `get_default_industries()`, `get_default_locations()` — never reads config.yaml; writes config.yaml via `yaml.dump` on completion)
- [ ] 3.3 `pipeline.py` — strip to imports (`logging`, `re`, `datetime`, `typing`, `extractor`, `enricher`, `lead_scorer`, `analyzer.WebsiteAnalyzer`, `config_loader.load_config`) + `run_pipeline()` only; append re-exports block + `if __name__ == "__main__": main()`

## Phase 4: Verification

- [ ] 4.1 `python pipeline.py --help` — all 12 CLI flags present
- [ ] 4.2 Delete `config.yaml`, run `python pipeline.py --interactive`, verify prompts + `config.yaml` written
- [ ] 4.3 `python -c "from pipeline import load_config, export_csv, print_summary, main, run_interactive, export_html, load_leads_from_csv"` — zero errors
- [ ] 4.4 `python pipeline.py --from-csv leads.csv --html report.html` — produces output (if CSV exists)
- [ ] 4.5 `git ls-files files/lead_scorer.py` — empty; `git grep LeadScorer` — only `lead_scorer.py` (root)
