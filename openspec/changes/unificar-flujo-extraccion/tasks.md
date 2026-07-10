# Tasks: Unificar flujo de extracción en un solo workflow interactivo

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~890 total (additions + deletions) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR #1 (D3) → PR #2 (D1+D2) → PR #3 (D4) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 (D3) | Pipeline + Extractor internals | PR #1 ~50 lines | Base: `main`. Aislado, no rompe nada externamente. |
| 2 (D1+D2) | CLI entry + `run_extraction()` | PR #2 ~770 lines | Base: `main` (después de PR #1). Mayoría es borrar `run_interactive`/`run_explore` y reemplazar con versión unificada (~300 líneas nuevas). |
| 3 (D4) | Output paths, config, tests | PR #3 ~60 lines | Base: `main` (después de PR #2). Actualizar mocks de tests para nearbysearch. |

---

## D1 — Entry point y CLI

- [x] **D1-T1: Entry point sin flags** — En `cli.py`, modificar `main()`: cuando no hay flags especiales (`--crm-send`, `--serve`, `--audit`, `--from-csv+--html`, `--dry-run`), invocar `await run_extraction()` en vez de cargar config.yaml y ejecutar pipeline directamente.
- [x] **D1-T2: Eliminar flags `--interactive` y `--explore`** — En `cli.py` argparse, borrar ambos `add_argument()` y el import de `config_loader.get_default_locations` si ya no se usa en main. No reemplazar — argparse ya muestra `unrecognized arguments` por defecto.
- [x] **D1-T3: Actualizar `--help`** — Modificar el `description` y eliminar menciones a `--interactive` y `--explore` del texto de ayuda. El help debe reflejar que `python cli.py` sin args arranca el flujo interactivo.

**Archivos**: `cli.py`
**Dependencias**: ninguna

---

## D2 — `run_extraction()` y helpers

- [x] **D2-T4: Crear `run_extraction()`** — En `cli.py`, crear función `async def run_extraction()` que unifica el flujo de `run_interactive()` y `run_explore()`: menú industrias → ciudad texto libre → geocoding → grid config (radio, overlap) → menú goal → deep audits (SEO, Ads, IG→Web) → límite (default 100) → resumen + confirmación → pipeline → post-pipeline. Eliminar `run_interactive()` y `run_explore()`.
- [x] **D2-T5: Extraer helpers compartidos** — En `cli.py` (o nuevo módulo si aplica), extraer funciones: `_menu_industries()` (multi-select con todas/personalizada), `_menu_goal()` (mapa 1-9 → goal string), `_validate_grid_radius()`, `_validate_overlap()`. Reusar desde `run_extraction()`.
- [x] **D2-T6: Integrar geocoding + grid config** — `run_extraction()` geocodifica la ciudad ingresada. Si éxito → genera grid con radio/overlap configurados por el usuario. Si falla → warning y flag para que pipeline use Text Search fallback.
- [x] **D2-T7: Post-pipeline unificado** — Después de pipeline: generar HTML report (preguntar), ofrecer audit websites, ofrecer CRM send (heredado de `run_explore()`), guardar config en `config.yaml` (preguntar). Instagram search siempre activo sin toggle.

**Archivos**: `cli.py`
**Dependencias**: D1-T1, D1-T2

---

## D3 — Pipeline y Extractor

- [x] **D3-T8: Simplificar `run_pipeline()`** — En `pipeline.py`: eliminar parámetros `grid`, `grid_radius`, `grid_overlap`, `grid_cell_limit`, `do_ig_web` de la firma. Eliminar rama `if grid:` y bloque `else:` de Text Search. Leer grid config de `config["extraction"]["grid_radius"]` (default 1500) y `config["extraction"]["grid_overlap"]` (default 0.2). IG search siempre activo en `_enrich_lead()`.
- [x] **D3-T9: Fallback en `search_with_grid()`** — En `extractor.py`: modificar `search_with_grid()` para que cuando `geocode_city()` retorne `None`, loguee warning y llame `self.search_businesses(keyword, city_name)` en vez de retornar `[]`. `search_businesses()` no cambia su firma.

**Archivos**: `pipeline.py`, `extractor.py`
**Dependencias**: D2-T4 (run_extraction necesita la firma nueva de run_pipeline)

---

## D4 — Output y Config Paths

- [ ] **D4-T10: Output naming unificado** — En `cli.py` (en `run_extraction()` y outputs directos): todo CSV de extracción usa `leads_output/leads_{YYYYMMDD_HHMMSS}.csv`. Eliminar cualquier path con prefijo `explore_`. Asegurar que el directorio `leads_output/` se crea si no existe (`os.makedirs`).
- [ ] **D4-T11: Config único** — Eliminar referencia a `config_explore.yaml` en `run_explore()` (se borra con D2-T4). No hay archivo `config_explore.yaml` existente en el repo. Toda config se guarda en `config.yaml`.
- [ ] **D4-T12: Actualizar tests** — En `tests/test_integration.py`: refactorizar `_make_get_side_effect()` para mockear URLs `geocode` (devuelve bounds) + `nearbysearch` (devuelve results) en vez de `textsearch`. Los 6 tests (`test_pipeline_extracts_and_scores_leads`, `test_deduplication_merges_similar_names`, `test_pipeline_respects_limit`, `test_seo_audit_populates_audit_data`, `test_empty_results_handled_gracefully`, `test_pipeline_handles_api_errors`) deben pasar con los nuevos mocks.

**Archivos**: `tests/test_integration.py`, `cli.py`
**Dependencias**: D3-T8, D3-T9 (los tests mockean pipeline + extractor)
