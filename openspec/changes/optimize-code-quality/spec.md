# Spec: optimize-code-quality

## Purpose

Refactor 4 areas of technical debt — inline HTML, magic numbers, orphaned files, and exact-match dedup — with zero behavioral changes to CLI flags, scoring, extraction, or HTML output.

## Non-Goals

- Config file migration for thresholds/weights (deferred to own change)
- Async aiohttp extraction (deferred)
- HTML redesign — same CSS, structure, colors, emojis
- Adding tests, CI, or type annotations
- Modifying any CLI flag, interactive prompt, or export format

## Requirements

### R1: Jinja2 HTML templates

`reporters.py` and `analyzer.py` MUST replace f-string HTML construction with Jinja2 templates rendered via `Environment().get_template(data)`. Three templates MUST be created under `templates/`: `base.html`, `lead_report.html`, `audit_report.html`. `requirements.txt` MUST include `Jinja2`.

#### Scenario: Identical HTML output

- GIVEN a lead pipeline run produces HTML via `export_html()` and `_generate_html()`
- WHEN both functions use Jinja2 `Environment().get_template(name).render(data)` instead of inline f-strings
- THEN the rendered HTML is byte-identical to a known-good pre-change snapshot for the same input data

#### Scenario: No inline HTML in Python

- GIVEN `reporters.py` and `analyzer.py` previously built HTML with f-strings containing `<html>`, `<style>`, `<div>` tags
- WHEN the Jinja2 migration is complete
- THEN no `"""<` triple-quote HTML strings remain in either file
- AND all data is passed as template context dicts, not string-interpolated

#### Scenario: CLI and export flags unchanged

- GIVEN flags `--html`, `--audit`, `--csv`, `--from-csv`
- WHEN Jinja2 replaces the rendering backend
- THEN all flags produce identical output format, filename behavior, and error handling

### R2: Module-level constants

`analyzer.py`, `lead_scorer.py`, `extractor.py`, and `enricher.py` MUST extract bare numeric literals as `UPPER_CASE` module-level constants near their usage location. Excludes `0`, `1`, and index-lookup integers. Config migration is deferred.

#### Scenario: Constants extracted from all four files

| File | Example literals to extract |
|------|---------------------------|
| `analyzer.py` | Timeouts, score thresholds, word count limits, char limits, max improvements |
| `lead_scorer.py` | Goal-specific bonus/penalty values (40, 20, 30, 15, 10, etc.) |
| `extractor.py` | Max pagination pages (3), pagetoken sleep (2s), timeout (15s) |
| `enricher.py` | Timeout (10s), min social handle length (3) |

- GIVEN `grep -nE '[^a-zA-Z_][2-9][0-9]?[^a-zA-Z_]'` reveals bare literals in the four files
- WHEN each literal is replaced with a named constant
- THEN no bare numeric literal > 1 remains in those files (excluding `0`, `1`, and dict/list index access)

#### Scenario: Behavioral equivalence

- GIVEN the extracted constants are used in scoring decisions, timeouts, pagination limits
- WHEN the same input data is processed before and after extraction
- THEN scoring, extraction depth, enrichment behavior, and error handling are identical

### R3: files/ cleanup

`files/QUICK_START_GUIDE.md` and `files/README.md` MUST be deleted (duplicates of root docs). `files/industry_filters_reference.md`, `files/search_tactics_reference.md`, `files/outreach_templates.md`, and `files/lead_template.csv` MUST be moved to `docs/`. `files/SKILL.md` MUST remain in place.

#### Scenario: files/ state after cleanup

- GIVEN the cleanup is executed
- WHEN `ls files/` is inspected
- THEN only `SKILL.md` and `lead_template.csv` remain
- AND `ls docs/` contains the 4 moved reference files

#### Scenario: No imports broken

- GIVEN no Python source imports from `files/` (confirmed during exploration)
- WHEN the file moves and deletions occur
- THEN all `import` and `from ... import` statements across `*.py` files continue to resolve
- AND no `FileNotFoundError` occurs at module load time

### R4: Fuzzy dedup

`requirements.txt` MUST include `rapidfuzz`. A `deduplicate(leads, threshold=85)` function MUST be added to `pipeline.py` (or a new `dedup.py`) using `token_sort_ratio`. It MUST sort leads by score descending before dedup (highest score survives). It MUST run after all leads are collected, before returning from `run_pipeline()`.

#### Scenario: Near-duplicate merge

- GIVEN leads contain `[{"name": "Café A", "score": 90}, {"name": "Cafe A", "score": 85}]`
- WHEN `deduplicate()` runs with default threshold 85
- THEN "Cafe A" is removed
- AND the result contains only "Café A" (score 90)

#### Scenario: Score-sort preserves best lead

- GIVEN leads `[{"name": "Best Bar", "score": 50}, {"name": "Best Bar", "score": 95}]`
- WHEN dedup runs
- THEN the surviving lead has score 95

#### Scenario: Configurable threshold

- GIVEN `deduplicate(leads, threshold=95)`
- WHEN comparing "Café A" (90) and "Cafe A" (85) with ratio ~91%
- THEN both leads are retained (ratio below threshold)

#### Scenario: Run after collection, before return

- GIVEN `run_pipeline()` collects leads from extractors then enriches then scores
- WHEN the pipeline finishes
- THEN dedup runs before the final `return leads` statement
- AND the returned list has no pair with `token_sort_ratio >= threshold`

## Scenario Summary

| Req | Deliverable | Scenarios | Coverage |
|-----|------------|-----------|----------|
| R1 | Jinja2 templates | Identical output, no inline HTML, flags unchanged | Happy + 2 edge |
| R2 | Module-level constants | Four-file extraction, behavioral equivalence | Happy + edge |
| R3 | files/ cleanup | Post-cleanup state, no imports broken | Happy + edge |
| R4 | Fuzzy dedup | Near-duplicate merge, score sort, configurable threshold, pipeline position | Happy + 3 edge |

Total: 12 scenarios across 4 requirements.
