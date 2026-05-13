# Lead Extractor

Extracción automática de leads para micro-empresas usando Google Places API. Busca, enriquece, puntúa y exporta leads en CSV y HTML.

## Features

- **Búsqueda automática** en Google Places por industria + ciudad
- **4 industrias preconfiguradas**: Barberías, Cafeterías, Servicios Profesionales, Salud y Belleza
- **25 ciudades** en Chile (o configura las tuyas)
- **Detección de redes sociales** desde los websites de los negocios
- **Enriquecimiento de emails** vía Hunter.io (opcional)
- **Scoring 0-100 pts** configurable con tiers HOT/WARM/COOL/COLD
- **Modo interactivo** — te pregunta y extrae
- **Reporte HTML** minimalista con estadísticas y tabla
- **Exportación CSV** y **HTML**

## Archivos

| Archivo | Propósito |
|---------|-----------|
| `pipeline.py` | CLI principal: extracción, modo interactivo, reporte HTML |
| `extractor.py` | Cliente Google Places API (text search + details) |
| `enricher.py` | Hunter.io + detección de redes sociales desde HTML |
| `lead_scorer.py` | Motor de scoring configurable (0-100 pts) |
| `config.yaml` | Configuración de industrias, ubicaciones y pesos de scoring |
| `requirements.txt` | Dependencias: `requests`, `pyyaml` |
| `files/` | Documentación original de referencia (guias de búsqueda manual) |

## Setup

```bash
git clone <repo-url>
cd extract-leads

# Opción A: venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Opción B: directo
pip install -r requirements.txt

# Configurar API key
export GOOGLE_PLACES_API_KEY="tu_key_aqui"

# Opcional: para enriquecimiento de emails
export HUNTER_API_KEY="tu_key_aqui"
```

### Obtener API keys

- **Google Places API**: https://console.cloud.google.com → habilitar "Places API" → crear credenciales. Tiene $200/mes de crédito gratis (~6000 búsquedas de texto + 11000 detalles).
- **Hunter.io**: https://hunter.io → free tier: 25 búsquedas/mes.

## Uso

### Modo interactivo (recomendado)

```bash
python pipeline.py --interactive
```

Te guía paso a paso: API key → industrias → regiones → cantidad de leads → genera CSV + HTML.

### Modo configuración

```bash
# Con el config.yaml por defecto
python pipeline.py --limit 100

# Con archivo de configuración personalizado
python pipeline.py --config mi_config.yaml --output leads.csv

# Sin límite (extrae todo lo que encuentre)
python pipeline.py
```

### Reporte HTML desde CSV existente

```bash
python pipeline.py --from-csv leads.csv --html reporte.html
```

### CLI completo

```
opciones:
  --config PATH       Ruta al YAML de configuración (default: config.yaml)
  --output PATH       Archivo CSV de salida (default: leads_output/leads.csv)
  --limit N           Máximo de leads a extraer (0 = sin límite)
  --google-key KEY    API key de Google Places (o env GOOGLE_PLACES_API_KEY)
  --hunter-key KEY    API key de Hunter.io (o env HUNTER_API_KEY)
  --interactive       Modo interactivo (hace preguntas)
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

Campos: `business_name`, `industry`, `phone`, `email`, `address`, `city`, `website`, `facebook_url`, `instagram_handle`, `google_rating`, `review_count`, `lead_score`, `lead_tier`, `scoring_notes`, `source`, `date_found`.

### HTML

Reporte visual con:
- Tarjetas de resumen (total leads, con teléfono, con web, rating promedio, tiers)
- Gráfico de barras por industria
- Tabla completa con indicadores de contacto (📞🌐📸👍) y tier coloreado
- Diseño responsive, sin dependencias externas

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
            pipeline.py (orquestador)
              │        │         │
         extractor  enricher  scorer
         (Places)  (Hunter)  (0-100)
              │        │         │
              └────────┴─────────┘
                     │
              leads_output/
              ├── leads.csv
              └── reporte.html
```

## Requisitos

- Python 3.8+
- Google Places API key (gratis hasta ~6000 búsquedas/mes)
- Opcional: Hunter.io API key

## Licencia

MIT
