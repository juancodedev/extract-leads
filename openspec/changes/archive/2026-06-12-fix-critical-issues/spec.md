# Spec: fix-critical-issues

## Purpose

Structural refactoring of the extract-leads codebase — no behavioral changes. Four tasks eliminate dead code, deduplicate booking domain data, consolidate industry/city constants, and split the pipeline.py monolith into focused modules.

## Non-Goals

- Adding tests, async/await migration, scoring logic changes, or HTML template restructuring
- Changing the behavior of any CLI flag, export format, or interactive prompt flow
- Deleting the active `lead_scorer.py` at project root (imported by pipeline.py)
- Adding config.yaml reading to `run_interactive()` (always uses defaults)

## Requirements

### R1: Delete orphaned `files/lead_scorer.py`

The system MUST remove the file `files/lead_scorer.py` (324 lines).

#### Scenario: Confirmed orphan deletion
- GIVEN the files/lead_scorer.py file exists with zero imports across all `.py` files
- WHEN `git rm files/lead_scorer.py` is executed
- THEN no imports or references to `files.lead_scorer` or `files/lead_scorer` exist in the codebase
- AND `git grep LeadScorer` only matches the active `lead_scorer.py` at project root

#### Scenario: Active scorer preserved
- GIVEN the root-level `lead_scorer.py` is imported by pipeline.py
- WHEN the deletion of `files/lead_scorer.py` is performed
- THEN `lead_scorer.py` (at root) is NOT modified

### R2: Shared booking data module

The system MUST create `booking_data.py` with authoritative `BOOKING_DOMAINS: Dict[str, str]` and `BOOKING_SKIP: Set[str]` and update both `enricher.py` and `analyzer.py` to import from it.

#### Scenario: Union of domain entries
- GIVEN analyzer.py has 20 BOOKING_DOMAINS entries and enricher.py has 20 entries (18 shared + 2 unique: `appointmentplus.com`, `bookingsystem`)
- WHEN booking_data.py is created
- THEN BOOKING_DOMAINS contains the union of both: all analyzer.py entries PLUS `appointmentplus.com`
- AND `bookingsystem` is EXCLUDED (was a partial substring causing false positives)
- AND analyzer.py's key names (human-readable labels) take precedence for shared entries

#### Scenario: Union of skip terms
- GIVEN analyzer.py BOOKING_SKIP has 17 terms and enricher.py has 13 terms (4 missing: "login", "registro", "register", "signin")
- WHEN booking_data.py is created
- THEN BOOKING_SKIP contains the union of both (17 terms)

#### Scenario: analyzer.py imports from booking_data
- GIVEN analyzer.py currently defines BOOKING_DOMAINS (lines 18-39) and BOOKING_SKIP (lines 57-62) inline
- WHEN both are removed
- THEN analyzer.py imports `BOOKING_DOMAINS` and `BOOKING_SKIP` from `booking_data`
- AND all usages of BOOKING_DOMAINS (line 264) and BOOKING_SKIP (line 272) continue to resolve

#### Scenario: enricher.py imports from booking_data
- GIVEN enricher.py defines `booking_domains` list (lines 134-142) and `booking_skip` set (lines 143-145) inline
- WHEN both are removed
- THEN enricher.py imports `BOOKING_DOMAINS` and `BOOKING_SKIP` from `booking_data`
- AND all booking-link detection logic (lines 147-158) continues to work with the imported values

### R3: Consolidate industry/city data

The system MUST remove hardcoded `AVAILABLE_INDUSTRIES` and `ALL_CITIES` from pipeline.py and make `run_interactive()` load from config_loader defaults.

#### Scenario: First-run fallback defaults
- GIVEN no config.yaml exists (fresh clone scenario)
- WHEN `run_interactive()` is called
- THEN the industry and city selection prompts render identically to current behavior
- AND the data matches the current hardcoded `AVAILABLE_INDUSTRIES` (12 industries with name, keywords, bonus_score) and `ALL_CITIES` (25 cities with city, region, premium) exactly

#### Scenario: Constants removed from pipeline.py
- GIVEN pipeline.py currently defines `AVAILABLE_INDUSTRIES` (lines 49-110) and `ALL_CITIES` (lines 112-138)
- WHEN both blocks are removed
- THEN `run_interactive()` (in cli.py) imports `get_default_industries()` and `get_default_locations()` from config_loader.py
- AND no references to `AVAILABLE_INDUSTRIES` or `ALL_CITIES` remain in pipeline.py

#### Scenario: Industry data schema preserved
- GIVEN the interactive mode references `ind['name']`, `ind['keywords']`, and `ind['bonus_score']` from industry entries
- WHEN the data moves to config_loader
- THEN each industry dict in get_default_industries() includes `name`, `keywords`, and `bonus_score` keys
- AND city dicts include `city`, `region`, and `premium` keys

### R4: Split pipeline.py into focused modules

The system MUST extract pipeline.py (~1019 lines) into four new modules: `cli.py`, `exporters.py`, `reporters.py`, `config_loader.py`. pipeline.py retains only `run_pipeline()` plus imports.

#### Scenario: Module boundaries preserved

| Module | Functions moved from pipeline.py | New functions |
|--------|---------------------------------|---------------|
| `config_loader.py` | `load_config()` | `get_default_industries()`, `get_default_locations()` |
| `cli.py` | `main()`, `run_interactive()` | — |
| `exporters.py` | `export_csv()`, `load_leads_from_csv()` | — |
| `reporters.py` | `print_summary()`, `export_html()` | — |
| `pipeline.py` | — (keeps `run_pipeline()` only) | — |

#### Scenario: Full backward-compatible imports
- GIVEN external code or scripts may `from pipeline import load_config, export_csv, print_summary, run_interactive, export_html, load_leads_from_csv, main`
- WHEN `__init__.py` is created in the project root (or an `openspec.py` package)
- THEN all seven public symbols are re-exported from the pipeline module
- AND `from pipeline import X` continues to work for every previously public symbol

#### Scenario: All CLI flags unchanged
- GIVEN the current 12 CLI flags (--config, --output, --limit, --google-key, --hunter-key, --interactive, --html, --from-csv, --audit, --goal, --seo, --ads, --ig-web)
- WHEN the argparse definition moves to cli.py main()
- THEN all flags, their defaults, help text, and argument types are identical
- AND `python pipeline.py --interactive`, `python pipeline.py --config config.yaml --limit 5`, `python pipeline.py --from-csv leads.csv --html report.html`, `python pipeline.py --audit report.html --from-csv leads.csv` all produce identical behavior

#### Scenario: Interactive mode loads defaults from config_loader
- GIVEN `run_interactive()` previously referenced `AVAILABLE_INDUSTRIES` and `ALL_CITIES` directly
- WHEN it moves to cli.py
- THEN it calls `get_default_industries()` and `get_default_locations()` from config_loader
- AND NEVER reads from config.yaml
- AND all 12 industry entries and 25 city entries are presented identically

## Scenario Summary

| Req | Task | Scenarios | Coverage |
|-----|------|-----------|----------|
| R1 | Delete `files/lead_scorer.py` | Orphan confirmed, active scorer preserved | Happy + boundary |
| R2 | Shared booking data module | Domain union, skip union, analyzer import, enricher import | Happy + 3 edge cases |
| R3 | Consolidate industry/city | First-run fallback, constants removed, schema preserved | Happy + edge |
| R4 | Split pipeline.py | Module boundaries, backward imports, CLI flags, interactive | Happy + 3 edge cases |

Total: 12 scenarios across 4 requirements.
