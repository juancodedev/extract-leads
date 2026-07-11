# Spec: Unificar flujo de extracción interactivo

## Dominios funcionales

### 1. Entry Point y CLI

#### Requirements

1. **R-CLI-01 — Entry point sin flags**: `python cli.py` sin argumentos MUST arrancar el flujo unificado `run_extraction()`.

2. **R-CLI-02 — Flags legacy eliminados**: Los flags `--interactive` y `--explore` MUST NOT existir como argumentos de argparse. Si un usuario los pasa, el sistema MUST mostrar un error claro indicando que esos flags ya no existen y que use `python cli.py` directamente.

3. **R-CLI-03 — Flags existentes se mantienen**: Los flags `--config`, `--output`, `--limit`, `--google-key`, `--hunter-key`, `--html`, `--from-csv`, `--audit`, `--version`, `--goal`, `--seo`, `--ads`, `--ig-web`, `--dry-run`, `--crm-send`, y `--serve` SHALL mantenerse sin cambios.

4. **R-CLI-04 — Modos no interactivos**: Los modos `--crm-send`, `--serve`, `--audit`, `--from-csv+--html`, y `--dry-run` SHALL seguir funcionando como antes, sin pasar por `run_extraction()`.

#### Scenarios

**Scenario 1.1: Entry point sin flags**
- GIVEN el usuario ejecuta `python cli.py` sin argumentos
- WHEN el parser de argparse no detecta ningún flag de modo especial (ni `--crm-send`, `--serve`, `--audit`, `--from-csv+--html`, `--dry-run`)
- THEN el sistema invoca `run_extraction()`

**Scenario 1.2: Flag legacy `--interactive`**
- GIVEN el usuario ejecuta `python cli.py --interactive`
- WHEN argparse encuentra el flag
- THEN el sistema MUST mostrar: `error: unrecognized arguments: --interactive` (o mensaje equivalente en argparse)
- AND el sistema MUST NOT ejecutar ninguna extracción

**Scenario 1.3: Modo `--crm-send` sin cambios**
- GIVEN el usuario ejecuta `python cli.py --crm-send leads.csv`
- WHEN el parser detecta `--crm-send`
- THEN el sistema ejecuta `crm_send_batch()` directamente, sin pasar por `run_extraction()`

#### Validation Rules

- `--interactive` y `--explore` MUST NOT aparecer en `add_argument()` de argparse.
- Cualquier otro flag existente MUST mantener su comportamiento actual sin cambios.
- El mensaje de error para flags legacy SHOULD ser descriptivo (no solo el default de argparse).

---

### 2. Flujo Interactivo — `run_extraction()`

#### Requirements

1. **R-FLOW-01 — Industrias**: El flujo MUST presentar un menú multi-select de industrias (igual al de `run_interactive()` actual), permitiendo seleccionar múltiples, "todas", o una industria personalizada con keywords propias.

2. **R-FLOW-02 — Una ciudad por vez**: El flujo MUST pedir UNA ciudad en texto libre (no multi-región). Modelo tomado de `run_explore()`.

3. **R-FLOW-03 — Geocoding → Grid**: El flujo MUST geocodificar la ciudad ingresada. Si el geocoding es exitoso, MUST ejecutar grid search.

4. **R-FLOW-04 — Fallback geocoding**: Si el geocoding falla (devuelve `None`), el flujo MUST hacer un solo intento con Text Search y mostrar advertencia al usuario.

5. **R-FLOW-05 — Goal y deep audits**: El flujo MUST preguntar goal (menú 1-9), y opcionalmente habilitar SEO audit, Meta Ads audit, e IG→Web prototype.

6. **R-FLOW-06 — Default limit**: El default de límite de leads SHOULD ser 100.

7. **R-FLOW-07 — Grid config**: El flujo MUST pedir radio de celda (default 1500m) y superposición (default 20%).

8. **R-FLOW-08 — Post-pipeline**: Después de la extracción, el flujo MUST ofrecer:
   - Generar reporte HTML
   - Auditar websites (deep SEO audit)
   - Enviar leads al CRM
   - Guardar configuración en `config.yaml`

9. **R-FLOW-09 — Instagram siempre activo**: La búsqueda proactiva de Instagram SHALL ejecutarse siempre, sin toggle para desactivarla (herencia del flujo explore pero sin opción de desactivar).

10. **R-FLOW-10 — Confirmación antes de ejecutar**: El flujo MUST mostrar un resumen de la configuración (industria, ciudad, radio, overlap, goal, límite, audits activos) y pedir confirmación antes de comenzar la extracción.

#### Scenarios

**Scenario 2.1: Happy path completo**
- GIVEN el usuario ejecuta `python cli.py`
- WHEN `run_extraction()` se ejecuta
- AND el usuario selecciona industrias, ingresa "Ñuñoa", goal "web", SEO audit sí, límite 100
- AND el geocoding devuelve bounds válidos
- THEN el sistema genera grid, ejecuta Nearby Search, y produce leads
- AND al final ofrece HTML report, audit, CRM send, y guardar config

**Scenario 2.2: Geocoding falla, fallback a Text Search**
- GIVEN el usuario ingresa una ciudad que no existe o no se puede geocodificar
- WHEN `geocode_city()` devuelve `None`
- THEN el sistema MUST mostrar: "No se pudo geocodificar la ciudad, usando búsqueda por texto como fallback"
- AND ejecuta `search_businesses()` (Text Search) para esa ciudad
- AND el flujo continúa normalmente (HTML, CRM, etc.)

**Scenario 2.3: Usuario cancela en confirmación**
- GIVEN el usuario completa toda la configuración interactiva
- WHEN se muestra el resumen y se pide confirmación
- AND el usuario responde "n"
- THEN el sistema MUST mostrar "Cancelado" y salir sin ejecutar extracción

#### Validation Rules

- Se MUST procesar UNA ciudad por ejecución. No más.
- El límite MUST ser un entero positivo. Si el usuario ingresa un valor no numérico, SHOULD usar default 100.
- El radio MUST estar entre 200m y 50000m. Si está fuera de rango, SHOULD usar default 1500.
- La superposición MUST estar entre 0.0 y 0.5.

---

### 3. Pipeline — `run_pipeline()`

#### Requirements

1. **R-PIPE-01 — Grid como default**: `grid` SHALL ser siempre `True`. El parámetro `grid` MUST ser eliminado de la firma de `run_pipeline()`.

2. **R-PIPE-02 — Parámetros de grid**: Los parámetros `grid_radius`, `grid_overlap`, y `grid_cell_limit` SHALL moverse al config (sección `grid:` dentro del `config` dict) o mantenerse como kwargs con defaults. No más branching `if grid:`.

3. **R-PIPE-03 — Rama Text Search eliminada**: El bloque `if grid: ... else: results = await extractor.search_businesses(...)` MUST ser eliminado. `search_with_grid()` es el único camino de extracción.

4. **R-PIPE-04 — Instagram siempre proactivo**: El parámetro `do_ig` en pipeline SHALL eliminarse. La búsqueda de Instagram se ejecuta en `_enrich_lead()` sin toggle.

5. **R-PIPE-05 — Firma simplificada**: La firma `run_pipeline()` MUST eliminar `grid`, `grid_radius`, `grid_overlap`, `grid_cell_limit` y `do_ig_web` de sus parámetros directos. Estos valores SHALL leerse del `config` dict o tener defaults fijos.

#### Scenarios

**Scenario 3.1: Pipeline sin parámetro grid**
- GIVEN se llama `run_pipeline(config, api_key, hunter_key, limit=100, goal="web")`
- WHEN el pipeline itera sobre locations
- THEN siempre llama `extractor.search_with_grid()` para cada keyword + location
- AND nunca llama `extractor.search_businesses()`

**Scenario 3.2: Grid radius desde config**
- GIVEN el config tiene `extraction.grid_radius: 2000` y `extraction.grid_overlap: 0.15`
- WHEN `run_pipeline()` lee el config
- THEN pasa esos valores a `search_with_grid()`
- AND si el config no tiene valores de grid, usa defaults (1500m, 20%)

#### Validation Rules

- `run_pipeline()` MUST NOT aceptar `grid` como keyword argument.
- `run_pipeline()` MUST NOT tener el bloque `if grid:`.
- El import de `search_businesses` en pipeline MUST ser removido o no usado.
- `do_ig_web` MUST ser eliminado de la firma de `run_pipeline()`.
- Instagram search SHALL ejecutarse en `_enrich_lead()` para cada lead, sin toggle.

---

### 4. Extractor — `search_businesses()`

#### Requirements

1. **R-EXT-01 — `search_businesses()` como fallback**: `search_businesses()` SHALL conservarse como método público en `PlacesExtractor`, pero solo se usa como fallback cuando `geocode_city()` devuelve `None`.

2. **R-EXT-02 — `search_with_grid()` como método principal**: `search_with_grid()` SHALL ser el método llamado por defecto desde pipeline.

3. **R-EXT-03 — Fallback en `search_businesses()`**: Si `search_with_grid()` recibe bounds `None` de `geocode_city()`, MUST delegar a `search_businesses()` y loguear una advertencia.

4. **R-EXT-04 — `search_businesses()` no cambia firma**: La firma de `search_businesses(keyword, location)` SHALL mantenerse igual. El método mismo no cambia.

#### Scenarios

**Scenario 4.1: Geocoding exitoso → grid**
- GIVEN `search_with_grid()` es llamado con ciudad "Santiago, Chile"
- WHEN `geocode_city()` devuelve bounds válidos
- THEN se genera grid y se ejecuta `nearby_search()` en cada celda
- AND `search_businesses()` NO se ejecuta

**Scenario 4.2: Geocoding falla → fallback**
- GIVEN `search_with_grid()` es llamado con ciudad "NonExistentCity"
- WHEN `geocode_city()` devuelve `None`
- THEN `search_with_grid()` MUST retornar los resultados de `search_businesses(keyword, city_name)`
- AND MUST loguear "Geocoding failed for 'NonExistentCity', falling back to Text Search"

**Scenario 4.3: `search_businesses()` solo se llama como fallback**
- GIVEN pipeline.py llama a `search_with_grid()` siempre
- WHEN el sistema funciona normalmente (geocoding exitoso)
- THEN `search_businesses()` nunca se invoca desde pipeline
- AND `search_businesses()` solo se ejecuta cuando `search_with_grid()` detecta geocoding fallido internamente

#### Validation Rules

- `search_businesses()` MUST NOT ser llamado directamente desde `pipeline.py`.
- `search_with_grid()` MUST contener la lógica de fallback internamente.
- El fallback MUST loguear una advertencia clara al usuario.

---

### 5. Output y Config Paths

#### Requirements

1. **R-OUT-01 — Output path único**: Todo output de extracción MUST usar el path `leads_output/leads_{timestamp}.csv` donde `timestamp` es `YYYYMMDD_HHMMSS`.

2. **R-OUT-02 — Sin output `explore_*`**: El formato antiguo `leads_output/explore_{city}_{timestamp}.csv` MUST ser eliminado.

3. **R-OUT-03 — Config único**: La configuración MUST guardarse siempre en `config.yaml`. El archivo `config_explore.yaml` MUST ser eliminado y no referenciado.

4. **R-OUT-04 — Directorio `leads_output/`**: El sistema MUST crear el directorio `leads_output/` si no existe.

#### Scenarios

**Scenario 5.1: Output unificado**
- GIVEN el usuario ejecuta el flujo unificado explorando "Ñuñoa"
- WHEN la extracción termina exitosamente
- THEN el CSV se guarda como `leads_output/leads_20260710_143022.csv`
- AND el nombre NO incluye "explore_ñuñoa" ni la ciudad

**Scenario 5.2: Config guardada en `config.yaml`**
- GIVEN el usuario completa una extracción y opta por guardar configuración
- WHEN el sistema escribe el archivo YAML
- THEN el archivo escrito es `config.yaml`
- AND `config_explore.yaml` nunca se crea ni se menciona

#### Validation Rules

- `config_explore.yaml` MUST NOT ser referenciado en ningún import, open(), o path.
- Todo output CSV de extracción MUST cumplir con `leads_output/leads_{timestamp}.csv`.
- No debe existir código que genere paths con prefijo `explore_`.

---

### 6. Flags Legacy

#### Requirements

1. **R-LEGACY-01 — Eliminación de `--interactive`**: `--interactive` MUST ser removido de `add_argument()` en argparse.

2. **R-LEGACY-02 — Eliminación de `--explore`**: `--explore` MUST ser removido de `add_argument()` en argparse.

3. **R-LEGACY-03 — Funciones `run_interactive()` y `run_explore()`**: Ambas funciones MUST ser eliminadas de `cli.py`. Su lógica combinada vive en `run_extraction()`.

#### Scenarios

**Scenario 6.1: Flag eliminado produce error claro**
- GIVEN se ejecuta `python cli.py --interactive`
- WHEN argparse procesa los argumentos
- THEN el sistema MUST mostrar un error de argumento no reconocido

**Scenario 6.2: Código legacy no referenciado**
- GIVEN se inspecciona `cli.py` después del cambio
- WHEN se busca la definición de `run_interactive` o `run_explore`
- THEN esas funciones MUST no existir
- AND no debe haber código muerto referenciándolas

#### Validation Rules

- `argparse.ArgumentParser` MUST NOT tener `add_argument('--interactive')` ni `add_argument('--explore')`.
- `cli.py` MUST NOT contener funciones `run_interactive()` ni `run_explore()`.

---

## Lo que NO cambia

| Área | Estado |
|------|--------|
| `enricher.py` | Sin cambios. Pipeline de enriquecimiento (email, website scan, social) idéntico. |
| `instagram_search.py` | Sin cambios. Búsqueda proactiva de Instagram se mantiene. |
| `lead_scorer.py` | Sin cambios. Scoring y clasificación por goal idénticos. |
| `reporters.py` | Sin cambios. `export_html()` y `print_summary()` idénticos. |
| `exporters.py` | Sin cambios. `export_csv()` y `load_leads_from_csv()` idénticos. |
| `analyzer.py` | Sin cambios. Auditoría SEO técnica idéntica. |
| `serve_report.py` | Sin cambios. Servir reporte HTML con integración CRM idéntico. |
| `config_loader.py` | Sin cambios. `load_config()`, `get_default_industries()`, `get_default_locations()` idénticos. |
| `tests/` | Sin cambios. Todos los tests existentes deben seguir pasando. |
| Deduplicación | `deduplicate_leads()` en pipeline.py sin cambios. |
| Normalización de redes sociales | `_normalize_social_as_website()` en pipeline.py sin cambios. |
| CRM helpers | `crm_send_batch()`, `_crm_authenticate()`, `_crm_send_lead()` en cli.py sin cambios. |
| Grid config desde CLI | La capacidad de configurar `grid_radius` y `grid_overlap` desde el flujo interactivo se mantiene (ahora en `run_extraction()`). |
