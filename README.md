# Lead Extractor & Business Auditor

Motor de prospección inteligente y auditoría digital. Busca, enriquece, califica y genera reportes de ventas automáticamente desde Google Places API.

[![CI](https://github.com/juancodedev/extract-leads/actions/workflows/ci.yml/badge.svg)](https://github.com/juancodedev/extract-leads/actions/workflows/ci.yml)

## Características

- **Async HTTP** — `aiohttp` con connection pooling, semáforos y retry exponencial (3 intentos, backoff 1.5×).
- **Opportunity Scoring** — Puntuación por objetivo de venta: web, SEO, ads o general. El sistema ajusta el ranking según lo que quieras vender.
- **Enriquecimiento multi-canal** — WhatsApp, Instagram, Facebook, LinkedIn desde el HTML del sitio. Email vía Hunter.io.
- **Deduplicación fuzzy** — `rapidfuzz` con umbral configurable para evitar leads repetidos.
- **Auditoría SEO técnica** — Title, meta description, OG tags, H1, canonical, schema.org, imágenes, lazy loading, viewport, gzip, CMS detection.
- **Detección de sistemas de reserva** — 21 plataformas: AgendaPro, Calendly, Setmore, SimplyBook, Acuity y más.
- **Reportes HTML** — Dashboards con Jinja2 + Material Icons: top oportunidades, tabla interactiva, badges de auditoría, scripts de contacto.
- **Integración con CRM** — Botón "Enviar al CRM" en cada lead del reporte HTML. Envío batch desde CLI. Servidor local proxy para evitar CORS.
- **Reporte responsivo** — En desktop tabla completa; en mobile cada lead se convierte en card vertical con label + valor.
- **Barra de progreso** — `tqdm` en pipeline de extracción y auditoría.
- **Modo interactivo** — Menú guiado que construye la configuración sin tocar YAML.

## Instalación

```bash
git clone https://github.com/juancodedev/extract-leads.git
cd extract-leads

# Opción A: pip editable (recomendado)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Opción B: requirements.txt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### API Keys

Crear `.env.local` (no se commitea):

```env
GOOGLE_PLACES_API_KEY="tu_key"
HUNTER_API_KEY="tu_key"       # opcional

# CRM (opcional — para enviar leads)
CRM_API_URL="https://crm.juancode.dev"
CRM_API_EMAIL="tu@email.com"
CRM_API_PASSWORD="tu-contraseña"
```

## Uso

### CLI entry point (si instalaste con `pip install -e .`)

```bash
lead-extractor --help
```

### Modo interactivo

```bash
python cli.py --interactive
```

Te guía paso a paso: industria, ciudad, objetivo de venta, auditorías y límite. Genera `config.yaml`, CSV, HTML y opcionalmente auditoría SEO.

### CLI directo

```bash
# Buscar 50 leads para vender SEO con auditoría activada
python cli.py --limit 50 --goal seo --seo

# Buscar oportunidades de diseño web
python cli.py --limit 100 --goal web

# Previsualizar sin gastar API quota
python cli.py --dry-run

# Generar reporte HTML desde CSV existente
python cli.py --from-csv leads.csv --html reporte.html

# Auditar websites desde CSV
python cli.py --from-csv leads.csv --audit auditoria.html

# Servir reporte HTML con botones CRM (abre navegador en localhost:8765)
python cli.py --serve leads_output/reporte.html

# Enviar leads en batch al CRM desde un CSV
python cli.py --crm-send leads_output/leads.csv
```

### Opciones completas

```
  --config PATH       YAML de configuración (default: config.yaml)
  --output PATH       CSV de salida (default: leads_output/leads.csv)
  --limit N           Máximo de leads (0 = sin límite)
  --google-key KEY    API key de Google Places (o env)
  --hunter-key KEY    API key de Hunter.io (o env)
  --interactive       Modo interactivo guiado
  --goal {web,seo,ads,general}
                      Objetivo de venta para el scoring (default: general)
  --seo               Auditoría SEO técnica para los top 10
  --ads               Marcar prospectos para Meta Ads
  --ig-web            Marcar prospectos para Instagram → Web
  --dry-run           Mostrar plan de búsqueda sin llamar APIs
  --audit FILE        Auditar websites desde CSV → HTML
  --html FILE         Generar reporte HTML desde CSV existente
  --from-csv FILE     CSV de entrada para --html o --audit
  --crm-send FILE     Enviar leads en batch al CRM desde CSV
  --serve [FILE]      Servir reporte HTML con proxy CRM (usa el más reciente si no se pasa ruta)
```

## Objetivos de scoring (`--goal`)

| Goal | Estrategia |
|------|-----------|
| `web` | Prioriza negocios **sin** sitio web (+40). Penaliza si ya tienen (-10). |
| `seo` | Prioriza negocios con web pero sin redes (+20) o con SEO técnico pobre (+30). Penaliza sin web (-20). |
| `ads` | Prioriza negocios con web (+20) y rating bajo 4.2 (+15). |
| `general` | Calidad de presencia digital: web (+15), redes (+20), WhatsApp (+10), rating 4.5+ (+5). |
| `automatizacion` | Prioriza negocios sin web (+40), sin booking (+30) y sin WhatsApp (+20) — oportunidad de automatización completa. |
| `reservas` | Prioriza negocios de servicio sin sistema de booking (+40). Penaliza si ya tienen (-30). |
| `menus` | Prioriza negocios de comida (+35) con sitio web sin precios (+30) ni galería (+20). |
| `inventarios` | Prioriza retail (+30) con sitio web (+20) y CMS básico (+15). |
| `pos` | Prioriza negocios con teléfono pero sin WhatsApp (+30), sin web (+25) o sin formulario de contacto (+20). |

**Tiers:** HOT (80-100) → WARM (60-79) → COOL (40-59) → COLD (0-39)

## Configuración (`config.yaml`)

### Industrias y ubicaciones

```yaml
search:
  industries:
    - name: "Barbería y Peluquería"
      keywords: ["barbería", "barber", "peluquería"]
      bonus_score: 5
  locations:
    - city: "Santiago"
      region: "Metropolitana"
      premium: true       # +10 en scoring
```

### Scoring

```yaml
scoring:
  base_score: 50
  max_score: 100
  dup_threshold: 85       # Umbral fuzzy dedup
  weights:
    website: 15
    active_social: 20
    whatsapp: 10
    multiple_channels: 10
    premium_location: 10
    owner_info: 5
  tiers:
    hot: [80, 100]
    warm: [60, 79]
    cool: [40, 59]
    cold: [0, 39]
```

### Extracción y enriquecimiento

```yaml
extraction:
  max_pages: 3            # Páginas de resultados de Google Places
  page_token_delay: 3     # Segundos entre páginas (Google tarda en activar tokens)
  request_timeout: 15     # Timeout HTTP
  max_retries: 3          # Reintentos con backoff
  retry_backoff: 1.5      # Factor de backoff exponencial

enrichment:
  hunter_timeout: 10
  website_scan_timeout: 10
  max_retries: 3
  retry_backoff: 1.5
```

## Output

### CSV (21 campos)

`business_name`, `industry`, `phone`, `email`, `address`, `city`, `website`, `whatsapp_link`, `facebook_url`, `instagram_handle`, `linkedin_url`, `booking_links`, `google_rating`, `review_count`, `lead_score`, `lead_tier`, `scoring_notes`, `needs_website`, `needs_seo`, `has_web_no_social`, `source`, `date_found`.

### HTML Dashboard

- Stats grid: total leads, con teléfono, WhatsApp, sitio web, booking, rating promedio.
- Top 5 Oportunidades con scoring notes y scripts de contacto personalizados.
- Distribución por industria y tier.
- Tabla completa con Material Icons clickeables (teléfono, WhatsApp, web, Instagram, Facebook).
- Badges de auditoría (SEO Auditado, Meta Ads Ready, IG-to-Web Ready).

## Integración con CRM

El proyecto puede enviar leads directamente a un CRM compatible (endpoint REST) desde el reporte HTML o desde la línea de comandos.

### Cómo funciona

1. Configurás `CRM_API_URL`, `CRM_API_EMAIL` y `CRM_API_PASSWORD` en `.env.local`
2. Al generar el reporte HTML, cada lead incluye un botón **"Enviar al CRM"**
3. El botón funciona a través de `serve_report.py` — un servidor local que:
   - Se autentica con tu CRM al iniciar (obtiene un JWT)
   - Sirve el reporte HTML en `http://localhost:8765`
   - Hace de proxy: el botón JS llama a tu localhost, el servidor reenvía al CRM con el token
   - **Soluciona el problema de CORS** — el navegador nunca toca el CRM directamente

### Mapeo de campos

| CSV / Lead         | CRM API       |
|--------------------|---------------|
| `business_name`    | `empresa`     |
| `email`            | `email`       |
| `source`           | `origen`      |
| `contact_person`   | `nombre`      |
| `phone`            | `telefono`    |
| `scoring_notes`    | `notas`       |
| `date_found`       | `fecha_captura` |
| *(fijo)*           | `status: "Nuevo"` |

### Botón desde el reporte HTML

```bash
# Con credenciales CRM en .env.local:
python cli.py --serve
# O directamente:
python serve_report.py leads_output/mi_reporte.html
```

Se abre el navegador en `http://localhost:8765`. Cada lead tiene un botón que lo envía al CRM con un solo click. Feedback visual: spinner → ✓ Enviado → ✗ Error (con restauración automática).

### Envío batch desde CLI

```bash
python cli.py --crm-send leads_output/leads.csv
```

Autentica, recorre todos los leads, los envía y muestra un resumen de cuántos se enviaron correctamente y cuáles fallaron.

### Sin credenciales CRM

Si no configurás las variables de CRM, el reporte HTML se genera sin los botones — el resto de la funcionalidad no se ve afectada.

### HTML Auditoría

Scorecards por sitio con: technical score (0-100), response time, SSL, sistema de reservas, imágenes, mobile-friendly, CMS detectado, canales de contacto, SEO title y checklist de mejoras priorizadas por severidad.

## Estructura del proyecto

```
extract-leads/
├── cli.py                  # CLI entry point + modo interactivo
├── pipeline.py             # Orquestador async principal
├── extractor.py            # Google Places API (async + retry)
├── enricher.py             # Email (Hunter.io) + social/booking scan
├── lead_scorer.py          # Scoring engine con flags de oportunidad
├── analyzer.py             # Website analyzer (SEO, imágenes, contacto)
├── reporters.py            # Reportes HTML (Jinja2) + resúmenes
├── serve_report.py         # Servidor local con proxy al CRM (soluciona CORS)
├── config_loader.py        # Carga de YAML con defaults y fallbacks
├── exporters.py            # CSV export/import
├── booking_data.py         # 21 sistemas de reserva + skip list
├── config.yaml             # Configuración de usuario
├── pyproject.toml          # Packaging, entry points, ruff, mypy
├── requirements.txt        # Dependencias runtime
├── templates/              # Jinja2: lead_report.html, audit_report.html
├── tests/                  # 36 tests (pytest)
├── agents/                 # Kits de auditoría especializada
├── docs/                   # Guías de outreach, filtros, tácticas
└── .github/workflows/      # CI: ruff + mypy + pytest
```

## Desarrollo

```bash
# Instalar con dependencias dev
pip install -e ".[dev]"

# Tests
pytest tests/ -v

# Lint
ruff check *.py

# Type check
mypy --ignore-missing-imports *.py
```

CI corre automáticamente en push y PR a `master` (ruff lint + mypy type-check + pytest).

## Licencia

MIT
