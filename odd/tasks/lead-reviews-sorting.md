# Feature: lead-reviews-sorting

## Objective

Make Google rating and review count first-class sortable fields for leads.

## Problem

`google_rating` and `review_count` are already extracted (`extractor.py`, `pipeline.py`) and exported to CSV,
but the HTML report is fixed-sorted by `lead_score` (`reporters.py:68`), there is no CLI sort option,
and the CRM payload drops both values.

## Scope

- HTML report: clickable column headers to sort the leads table client-side (Rating, Reviews, Score, ...).
- CLI: `--sort-by {score,rating,reviews}` that orders the CSV and the HTML report.
- CRM: include rating and review count in the `notas` field (CRM API has no dedicated columns —
  verified against `https://crm.juancode.dev/api/docs/openapi.json`, `CreateLeadRequest`).

Out of scope: adding columns to the CRM (separate repository).

## Constraints

- Missing ratings/reviews sort last, regardless of direction.
- CSV-loaded leads have string values; sorting must coerce numbers safely.
- Default behavior unchanged (`score`, descending).

## Tasks

- [x] T1 — CLI `--sort-by` + shared sort helper applied to CSV export and HTML report (route: delegated writer, 2+ non-trivial files)
- [x] T2 — Clickable sortable headers in `templates/lead_report.html` (route: delegated writer)
- [x] T3 — Rating and review count in CRM `notas` (CLI `_crm_send_lead` and report `sendToCRM` JS) (route: delegated writer)

## Acceptance criteria

- `python cli.py ... --sort-by reviews` produces CSV and HTML ordered by review count, descending.
- Clicking Rating/Reviews/Score headers in the report toggles ascending/descending order.
- CRM leads show `Rating: X (N reseñas)` in their notes.

## Checks

- `python3 -m pytest -q` (baseline: 50 passed)

## Progress

- Branch: `feat/lead-reviews-sorting`
- T1 (route: delegated writer). Helper `sort_leads`/`SORT_KEYS` placed in `exporters.py` (already in
  `pyproject.toml` py-modules; a new module would break non-editable installs). `--sort-by` applied to the
  interactive extraction CSV + HTML and the `--from-csv --html` path; `export_html(..., sort_by="score")`.
  RED: `tests/test_sorting.py` collection error `ModuleNotFoundError: No module named 'sorting'`
  (later relocated to `exporters`). GREEN: `64 passed`. `cli.py --help` lists `--sort-by`. Commit `5e60d31`.
- T2 (route: delegated writer). Sortable headers (#, Negocio, Ciudad, Rating, Reviews, Score) with
  `aria-sort` + CSS ▲/▼ indicator, keyboard (Enter/Space); cells carry `data-sort` (numeric via
  `exporters.sort_value`, '' when missing); sort script lives outside `{% if crm_enabled %}`.
  JS exception: no JS test runner in repo. Structural RED/GREEN via Python-rendered report:
  RED `TestReportSortableColumns` (3 failed) → GREEN `67 passed`. Extra: `node --check` on the rendered
  scripts OK; ad-hoc node DOM-stub run confirmed desc/asc toggle with empty values last.
  Limitation: on mobile (<768px) `thead` is hidden, so sorting is desktop-only; `--sort-by` still applies. Commit `30e944c`.
- T3 (route: delegated writer). Extracted pure `cli._build_crm_notes(lead)`; appends
  `Rating: X (N reseñas)` (singular `reseña` for 1; `Rating: X` when reviews missing/0) only when a numeric
  rating exists. Report `leads_json` now carries `google_rating`/`review_count`; template `crmRatingNote`
  mirrors the Python logic (report notes keep their existing trailing `scoring_notes`).
  RED: `tests/test_crm_notes.py` collection ImportError (`_build_crm_notes`). GREEN: `74 passed`.
  Extra: node eval of `crmRatingNote` matched Python outputs. Commit `71b9838`.
- Review: range master..459252b assessed medium (slice_budget_reached); consent granted; review-reliability
  approved and acknowledged (lineage review-000e0be6084d6566). Non-blocking follow-ups:
  `_build_crm_notes` OverflowError on 'inf' review count (cli.py:85-88); JS/Python note parity drift on
  malformed input; client-side sort comparator not executed by tests; CSV ordering in run_extraction untested.
- Follow-up fix (route: inline, 2 one-line edits + test): `exporters.to_number` now rejects non-finite
  values (was only NaN), fixing `_build_crm_notes` OverflowError on 'inf' review counts; JS `crmRatingNote`
  uses `Number.isFinite`. RED: `test_non_finite_review_count_is_ignored` OverflowError + 'inf' rating leaked
  (2 failed). GREEN: `75 passed`. node check: 'Infinity' rating -> '' ; 'Infinity' reviews ignored.
- Parent spot check: `python3 -m pytest -q` -> 74 passed.
- Next step: optional follow-ups above; push/PR are user decisions.
