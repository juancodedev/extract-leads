# Design: Unificar flujo de extracción en un solo workflow interactivo

## Technical Approach

Fusionar `run_interactive()` y `run_explore()` en una sola `run_extraction()` que unifica el entry point de CLI, elimina los flags `--interactive` y `--explore`, y establece Grid + Nearby Search como el único método de extracción con fallback a Text Search cuando geocoding falla. Los cambios son puramente de orquestación — los módulos de enriquecimiento, scoring y reporting no se modifican.

## Architecture Decisions

### Decision: Grid siempre activo en pipeline
**Choice**: Eliminar el parámetro `grid` de `run_pipeline()` y la rama `if grid:`.
**Alternatives**: Mantener flag con default `True`, o deprecar gradualmente.
**Rationale**: La spec R-PIPE-01 exige grid como default y R-PIPE-03 elimina la rama Text Search. El código actual ya tiene `search_with_grid()` maduro y probado en el flujo explore.

### Decision: Fallback dentro de `search_with_grid()` no en pipeline
**Choice**: `search_with_grid()` detecta geocoding fallido y delega a `search_businesses()` internamente.
**Alternatives**: Mantener el fallback en pipeline.py con un `if/else`.
**Rationale**: La spec R-EXT-03 exige que el fallback esté encapsulado en el extractor. Pipeline no debe saber nada de Text Search.

### Decision: Instagram search siempre proactivo sin toggle
**Choice**: Eliminar el parámetro `do_ig_web` de `run_pipeline()` y quitar toggle en UI.
**Alternatives**: Mantener toggle como `True` default.
**Rationale**: El código actual en `_enrich_lead()` (líneas 319-326) ya ejecuta Instagram search para cada lead sin depender de `do_ig_web`. El flag solo controlaba el mark `requires_ig_web_prototype`. Se elimina el toggle de UI y se mantiene el search siempre activo.

### Decision: Naming de output unificado
**Choice**: Siempre `leads_output/leads_{YYYYMMDD_HHMMSS}.csv`.
**Alternatives**: Incluir ciudad o industria en el nombre.
**Rationale**: La spec R-OUT-01 exige output fijo. El timestamp único evita colisiones y es el formato que ya usa `run_interactive()`. La ciudad se puede identificar dentro del CSV.

## Data Flow — `run_extraction()`

```
python cli.py (sin args)
    │
    ▼
[Args sin flags especiales?] ──sí──► run_extraction()
    │                                   │
    no                                  │
    ▼                                   ▼
[--crm-send/--serve/           [API key check]
 --audit/--from-csv             [Menú industrias ← get_default_industries()]
 --dry-run]                      [Ciudad en texto libre]
    │                             [Geocode city → Bounds]
    │                             ├── éxito ──► generate_grid(radius, overlap)
    │                             └── None ──► Text Search fallback + warning
    ▼                              [Menú goal (1-9)]
[Comportamiento                    [Deep audits: SEO, Ads, IG→Web]
 existente sin                     [Límite leads (default 100)]
 cambios]                          [Resumen + confirmación]
                                    │
                                    ▼
                            run_pipeline(config, api_key, hunter_key, limit, goal, do_seo, do_ads)
                                    │
                                    ▼
                            search_with_grid() ←── geocoding OK
                            └── search_businesses() ←── geocoding None (fallback)
                                    │
                                    ▼
                            [_enrich_lead()] × N (IG search siempre activo)
                                    │
                                    ▼
                            [HTML report?]
                            [Audit websites?]
                            [CRM send?]
                            [Save config → config.yaml]
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `cli.py` | Modify | Crear `run_extraction()` fusionando `run_interactive()` + `run_explore()`. Eliminar ambas funciones legacy. Quitar flags `--interactive`, `--explore` de argparse. `python cli.py` sin args → `run_extraction()`. |
| `pipeline.py` | Modify | Eliminar parámetro `grid`, `grid_radius`, `grid_overlap`, `grid_cell_limit`, `do_ig_web`. Eliminar rama `if grid:`. Simplificar firma de `run_pipeline()`. |
| `extractor.py` | Modify | `search_with_grid()`: agregar fallback a `search_businesses()` cuando `geocode_city()` devuelve `None` (hoy retorna `[]`). |
| `config_explore.yaml` | Delete | Ya no se referencia ni se crea. Todo usa `config.yaml`. |

## Interfaces / Contracts

### `run_pipeline()` — firma simplificada

```python
async def run_pipeline(
    config: dict,
    api_key: str,
    hunter_key: str = "",
    limit: int = 0,
    goal: str = "general",
    do_seo: bool = False,
    do_ads: bool = False,
) -> list[dict]:
```

**Cambios**:
- Eliminado: `do_ig_web` (IG search siempre activo en `_enrich_lead`)
- Eliminado: `grid`, `grid_radius`, `grid_overlap`, `grid_cell_limit` (grid es el único camino)
- Grid config se lee de `config["extraction"]["grid_radius"]` y `config["extraction"]["grid_overlap"]` con defaults fijos (1500m, 0.2)

### `search_with_grid()` — firma con fallback

```python
async def search_with_grid(
    self,
    keyword: str,
    city_name: str,
    radius_m: int = DEFAULT_GRID_RADIUS,
    overlap: float = DEFAULT_GRID_OVERLAP,
    cell_limit: int = 50,
) -> list[dict]:
```

**Cambios**: Si `geocode_city()` retorna `None`, loguea warning y llama `self.search_businesses(keyword, city_name)` en vez de retornar `[]`.

### `run_extraction()` — nueva función

```python
async def run_extraction():
    """Flujo unificado: input interactivo → geocoding → grid → pipeline → post-pipeline."""
```

No acepta parámetros. Lee API keys de .env o input. Contiene:
- Shared helpers extraídos (menú industrias, menú goal, validación de inputs)
- Flujo: ciudad → geocode → grid config → goal → audits → limit → confirm → pipeline → post-pipeline

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Integration | Pipeline con grid activo | Mockear geocode + nearbysearch URLs en vez de textsearch. Actualizar `_make_get_side_effect()`. |
| Integration | Fallback a Text Search | Mockear geocode → None response → verificar que `search_businesses()` se ejecuta (mock textsearch URL). |
| Unit | `search_with_grid()` fallback | Test directo en extractor: mock `geocode_city()` → None → assert llama `search_businesses()`. |

### Tests existentes que se rompen

1. **`test_pipeline_extracts_and_scores_leads`** — Mockea `textsearch` URL. Tras el cambio, pipeline llama a `search_with_grid()` que llama a `geocode` + `nearbysearch`. Mock debe responder a ambas.
2. **`test_deduplication_merges_similar_names`** — Mismo problema: mock de `textsearch` no aplica.
3. **`test_pipeline_respects_limit`** — Usa `query` params de textsearch. NearbySearch usa `keyword` + `location` + `radius`. Mock debe refactorizarse para nearbysearch URL y params.
4. **`test_seo_audit_populates_audit_data`** — Mismo problema de mock.
5. **`test_empty_results_handled_gracefully`** — Mock de `textsearch`.
6. **`test_pipeline_handles_api_errors`** — Mock de `textsearch`.

**Solución para tests**: Refactorizar `_make_get_side_effect()` para manejar:
- URL `geocode` → devuelve bounds OK con viewport
- URL `nearbysearch` → devuelve results (lo que antes devolvía textsearch)
- URL `textsearch` → solo se usa como fallback (mantener mock opcional)

## Migration / Rollout

No migration required. Los cambios son atómicos en 3 archivos. Rollback: `git revert` del commit que contiene los cambios.

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Ciudad vacía | `run_extraction()` valida input no vacío; si vacío, `sys.exit(1)` con error |
| Geocoding → None | Warning + Text Search fallback. Flujo continúa normalmente (HTML, CRM, etc.) |
| Ctrl+C | `asyncio` cancela tareas pendientes; el handler por defecto de Python muestra KeyboardInterrupt |
| Sin API keys | `run_extraction()` pide key al inicio; si vacía, lee de .env; si ambas vacías, `sys.exit(1)` |
| Límite 0 | Sin límite (hereda comportamiento actual: pipeline con `limit=0` = unlimited) |
| `--interactive` legacy | ArgumentParser no reconoce el flag → argparse muestra error `unrecognized arguments: --interactive` |
| `--explore` legacy | Mismo comportamiento que `--interactive` |

## Open Questions

- [ ] ¿Mantener `grid_cell_limit` como parámetro de `search_with_grid()` o moverlo a config? Por ahora se mantiene como parámetro con default 50.
