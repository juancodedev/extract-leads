# Proposal: Unificar flujo de extracción en un solo workflow interactivo

## Intent

Dos flujos separados (`--interactive` y `--explore`) en `cli.py` comparten ~60% de código pero generan inconsistencia: distinto método de búsqueda, distinto output naming, distinto post-procesamiento (solo explore tiene CRM send), y dudas sobre cuál usar. El objetivo es un solo entry point interactivo con Grid + Nearby Search como método único, rescatando lo mejor de cada flujo.

## Scope

### In Scope
- `cli.py`: fundir `run_interactive()` y `run_explore()` en `run_extraction()`; eliminar flags `--interactive` y `--explore`
- `pipeline.py`: `grid=True` como default; eliminar rama Text Search; simplificar firma de `run_pipeline()`
- `extractor.py`: `search_businesses()` delega a `search_with_grid()` siempre; Text Search solo como fallback si geocoding falla
- Output paths: unificar a `leads_output/leads_{timestamp}.csv` (eliminar `explore_{city}_...`)
- Config: unificar a `config.yaml` (eliminar `config_explore.yaml`)
- `python cli.py` sin flags → arranca el flujo unificado

### Out of Scope
- Pipeline de enriquecimiento (`enricher.py`, `instagram_search.py`)
- Scoring (`lead_scorer.py`)
- Reportes HTML (`reporters.py`)
- Auditoría (`analyzer.py`, `serve_report.py`)
- Exporters (`exporters.py`)
- Tests existentes (`tests/`)

## Capabilities

### New Capabilities
None — no se introducen nuevas capacidades de especificación.

### Modified Capabilities
None — los contratos de extracción, enriquecimiento y scoring no cambian. Los cambios son puramente de orquestación CLI y defaults de pipeline.

## Approach

1. Extraer toda la lógica interactiva de `run_interactive()` y `run_explore()` en una nueva `run_extraction()` que:
   - Pida industrias (menú multi-select existente)
   - Pida UNA ciudad en texto libre (modelo explore)
   - Geocodee la ciudad → viewport → grilla
   - Pida goal, deep audits, límite (default 100)
   - Ejecute pipeline con grid SIEMPRE
   - Post-pipeline: HTML report, audit websites, CRM send, guardar config
2. Eliminar `run_interactive()` y `run_explore()`.
3. En `pipeline.py`, eliminar el parámetro `grid` y la rama `if grid:` — `search_with_grid()` es el único camino.
4. En `extractor.py`, `search_businesses()` delega a `search_with_grid()` con fallback a Text Search si geocoding falla.
5. Unificar output paths y config saving.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `cli.py` | Modified | Fundir `run_interactive` y `run_explore` en `run_extraction`. Eliminar flags `--interactive`, `--explore`. `python cli.py` sin args arranca el flujo unificado. |
| `pipeline.py` | Modified | Eliminar parámetro `grid` y rama `if grid:`. Grid siempre activo. |
| `extractor.py` | Modified | `search_businesses()` delega a `search_with_grid()`. Text Search solo como fallback de geocoding. |
| `leads_output/` | Modified | Unificar naming a `leads_{timestamp}.csv` (no más `explore_{city}_...`). |
| `config_explore.yaml` | Removed | Eliminar; todo usa `config.yaml`. |

## Reglas de negocio

| Decisión | Valor |
|---|---|
| Entry point | `python cli.py` sin flags → arranca flujo unificado |
| Método de búsqueda | Grid + Nearby Search SIEMPRE |
| Fallo de geocoding | Fallback a Text Search |
| Ciudades | Una por vez (modelo explore) |
| Default limit | 100 leads |
| Flags legacy | Eliminar `--interactive` y `--explore` |
| Deep audits | SEO, Meta Ads, IG→Web (mantener) |
| CRM send | Integrado al final del flujo |
| Instagram search | Siempre proactivo (sin toggle) |
| Config saving | `config.yaml` único |
| Output naming | `leads_output/leads_{timestamp}.csv` único |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Grid search genera más llamadas API (mayor costo) | Medium | Mantener default limit 100; el usuario puede ajustar radio/overlap |
| Backward compatibility si scripts existentes usan `--interactive` o `--explore` | Medium | Eliminar flags con advertencia clara en error de argparse |
| Text Search como fallback no cubre edge cases de geocoding | Low | Text Search ya existe y funciona; solo se activa si geocoding devuelve None |

## Rollback Plan

Revertir cambios en `cli.py`, `pipeline.py`, `extractor.py` usando `git revert`. Restaurar `config_explore.yaml` si existe. Los cambios son atómicos en 3 archivos principales.

## Dependencies

- Ninguna externa. Los módulos de enriquecimiento/scoring/reporting no cambian.

## Success Criteria

- [ ] `python cli.py` sin flags arranca el flujo unificado interactivo
- [ ] El flujo pide industria, ciudad, goal, audits, límite y ejecuta grid search
- [ ] Fallback a Text Search funciona cuando geocoding falla
- [ ] Output siempre en `leads_output/leads_{timestamp}.csv`
- [ ] Config guardada en `config.yaml`
- [ ] CRM send se ofrece al final del flujo
- [ ] `--interactive` y `--explore` ya no existen como flags
- [ ] Todos los tests existentes pasan
