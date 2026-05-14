# Lead Extractor & Business Auditor

Motor de prospección inteligente y auditoría digital. Busca, califica, audita y genera reportes de ventas personalizados automáticamente.

## 🚀 Features Avanzadas

- **Opportunity Scoring (Puntuación por Objetivo)**: Ajusta el ranking de leads según lo que quieras vender (Diseño Web, SEO, Ads o General). 
  - *Ej: Si vendes webs, el sistema prioriza negocios que NO tienen sitio.*
- **Auditoría SEO Técnica**: Análisis profundo de meta-tags, estructura de headings (H1-H6), rendimiento y SEO social de los mejores prospectos.
- **Top 5 Oportunidades**: Dashboard visual que destaca los 5 mejores prospectos con análisis de brechas y **scripts de contacto personalizados**.
- **Material UI Icons**: Interfaz de reporte modernizada con iconos oficiales de marca (WhatsApp, Instagram, etc.) y Material Design.
- **Detección de Sistemas de Reserva**: Identifica si el negocio usa AgendaPro, Calendly, Setmore y otros.
- **Enriquecimiento Multi-canal**: WhatsApp, Instagram, Facebook, LinkedIn y emails vía Hunter.io.

## 📋 Auditorías Integradas

| Auditoría | Qué hace |
|-----------|----------|
| **SEO Audit** | Analiza técnicamente la web para detectar fallos de posicionamiento. |
| **Meta Ads Audit** | (Badge) Identifica si el negocio está listo para campañas de pago. |
| **Business Audit** | (Badge) Evalúa la coherencia de la presencia digital completa. |
| **Instagram → Web** | (Badge) Detecta candidatos ideales para convertir su perfil de IG en una web profesional. |

## Archivos

| Archivo | Propósito |
|---------|-----------|
| `pipeline.py` | CLI principal: Orquestación, Auditoría y Reportes |
| `analyzer.py` | Motor de auditoría técnica y análisis de websites |
| `extractor.py` | Cliente Google Places API |
| `enricher.py` | Detección de redes, WhatsApp y emails (Hunter.io) |
| `lead_scorer.py` | Motor de scoring dinámico basado en objetivos |
| `config.yaml` | Configuración de industrias, ubicaciones y pesos |
| `agents/` | Plantillas especializadas para auditorías profundas |

## Setup

```bash
git clone <repo-url>
cd extract-leads

# Crear y activar venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configurar API keys
# Puedes crear un archivo .env.local (recomendado) o .env con:
# GOOGLE_PLACES_API_KEY="tu_key_aquí"
# HUNTER_API_KEY="tu_key_aquí"

export GOOGLE_PLACES_API_KEY="tu_key_aqui"
```

## Uso

### Modo Prospecting Engine (Recomendado)

```bash
python pipeline.py --interactive
```

El nuevo flujo integrado te permite:
1. Configurar tu búsqueda (Industria + Ciudad).
2. Elegir tu **Objetivo de Venta** (Web, SEO, Ads).
3. Activar **Auditorías Profundas** para los mejores resultados.

### CLI Avanzado

```bash
# Buscar leads para vender SEO con auditoría técnica activada
python pipeline.py --limit 50 --goal seo --seo

# Buscar oportunidades de diseño web
python pipeline.py --limit 100 --goal web

# Generar reporte desde CSV con el nuevo diseño
python pipeline.py --from-csv leads.csv --html reporte.html
```

## Configuración de Objetivos (`--goal`)

- **`web`**: Prioriza negocios sin sitio web (Opportunity Scoring invertido).
- **`seo`**: Prioriza negocios con web pero con fallos técnicos o sin redes sociales.
- **`ads`**: Prioriza negocios con web pero bajo rating o poca visibilidad.
- **`general`**: Puntuación clásica basada en la calidad de la presencia digital.

## Reporte HTML

El reporte ahora es un **Sales Dashboard** que incluye:
- **Top Oportunidades**: Tarjetas detalladas con la "falla principal" del negocio y cómo abordarlos.
- **Material Icons**: Visualización profesional de canales de contacto.
- **Badges de Auditoría**: Identificación visual de leads auditados o listos para servicios específicos.

### CLI completo

```bash
opciones:
  --config PATH       Ruta al YAML de configuración (default: config.yaml)
  --output PATH       Archivo CSV de salida (default: leads_output/leads.csv)
  --limit N           Máximo de leads a extraer (0 = sin límite)
  --google-key KEY    API key de Google Places (o env GOOGLE_PLACES_API_KEY)
  --hunter-key KEY    API key de Hunter.io (o env HUNTER_API_KEY)
  --interactive       Modo interactivo (hace preguntas)
  --goal GOAL         Objetivo de venta: web, seo, ads, general (default: general)
  --seo               Activa auditoría SEO técnica profunda para el Top 10
  --ads               Marca prospectos para auditoría de Meta Ads
  --ig-web            Marca prospectos para prototipo Instagram-to-Web
  --html FILE         Genera reporte HTML desde CSV existente
  --from-csv FILE     Path al CSV para usar con --html
```

## Configuración (`config.yaml`)

### Industrias

```yaml
search:
  industries:
    - name: "Nombre de Industria"
      keywords: ["palabra1", "palabra2"]
      bonus_score: 5        # Puntos extra al score
```

### Ubicaciones

```yaml
  locations:
    - city: "Santiago"
      region: "Metropolitana"
      premium: true         # Da bonus de ubicación en el scoring
```

### Scoring

```yaml
scoring:
  base_score: 50            # Puntaje base
  max_score: 100            # Máximo posible
  weights:
    website: 15             # +15 si tiene sitio web
    active_social: 20       # +20 si tiene Instagram/Facebook
    multiple_channels: 10   # +10 si tiene 2+ canales de contacto
    premium_location: 10    # +10 si está en zona premium
    owner_info: 5           # +5 si hay persona de contacto
  tiers:
    hot: [80, 100]          # Contacto inmediato
    warm: [60, 79]          # Contacto esta semana
    cool: [40, 59]          # Email batch
    cold: [0, 39]           # Archivo
```

## Output

### CSV

Campos: `business_name`, `industry`, `phone`, `email`, `address`, `city`, `website`, `whatsapp_link`, `facebook_url`, `instagram_handle`, `google_rating`, `review_count`, `lead_score`, `lead_tier`, `scoring_notes`, `source`, `date_found`.

### HTML

Reporte visual con:
- **Top Oportunidades**: Tarjetas detalladas con análisis y script de contacto.
- **Resumen Estadístico**: Total leads, con teléfono, con web, rating promedio, distribución por tier.
- **Gráfico de Industrias**: Distribución visual de los hallazgos.
- **Tabla Pro**: Listado completo con Material Icons (MUI) y colores de marca oficiales.

## Ejemplo de resultados

De una extracción de 200 leads balanceados en 4 industrias:

| Industria | Leads | Phone | Website | Instagram | Rating |
|-----------|-------|-------|---------|-----------|--------|
| Barbería y Peluquería | 54 | 88% | 75% | 42% | 4.8★ |
| Cafetería y Restaurante | 38 | 85% | 72% | 38% | 4.7★ |
| Servicios Profesionales | 31 | 82% | 78% | 25% | 4.8★ |
| Salud y Belleza | 31 | 79% | 70% | 35% | 4.9★ |

## Arquitectura

```
                config.yaml
                     │
            pipeline.py (Orquestador)
          /          |           \
    extractor     enricher      analyzer
    (Places)     (Social/Email) (Auditoría SEO)
          \          |           /
            ──> lead_scorer <──
                (Goal-based)
                     │
              leads_output/
              ├── leads.csv
              └── reporte_ventas.html (MUI Design)
```

## Licencia

MIT
