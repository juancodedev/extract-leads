# Lead Extractor & Business Auditor — Claude Guide

Este proyecto está optimizado para ser usado por Claude Code. Como agente, tienes acceso a herramientas de extracción de leads, auditoría SEO, auditoría de anuncios, búsqueda de Instagram y generación de prototipos web.

## 🛠 Skills Disponibles

Puedes activar estas capacidades directamente:

1.  **Prospección Inteligente**: Busca negocios reales, analízalos y genera un informe de oportunidades.
    - *Ejemplo*: "Busca 20 barberías en Santiago para venderles web"
    - *Comando*: `python cli.py --limit 20 --goal web`

2.  **Exploración por Cuadrantes** (`--explore`): Busca una ciudad entera dividiéndola en celdas y buscando en cada una con Nearby Search. Mucho más leads que la búsqueda normal.
    - *Ejemplo*: "Explora Ñuñoa buscando barberías para venderles web"
    - *Comando*: `python cli.py --explore`

3.  **Búsqueda Proactiva de Instagram**: Si un negocio no tiene Instagram en su web, lo busca automáticamente en Instagram por nombre + ciudad.
    - *Ejemplo*: "Búscame el Instagram de esta peluquería"
    - *Integrado*: Se ejecuta automáticamente en cada extracción.

4.  **Auditoría SEO Técnica**: Realiza un análisis profundo de cualquier sitio web.
    - *Ejemplo*: "Audita el SEO de https://ejemplo.com"
    - *Skill*: Usa la lógica definida en `agents/kit-auditoria-seo/`

5.  **Auditoría de Meta Ads**: Analiza anuncios activos y su coherencia con la landing page.
    - *Ejemplo*: "Analiza los anuncios de [Negocio] y su web [URL]"
    - *Skill*: Usa la lógica definida en `agents/kit-auditoria-meta-ads/`

6.  **Instagram → Web**: Convierte un perfil de Instagram en un prototipo de sitio web profesional.
    - *Ejemplo*: "Convierte @usuario en una web de marca personal"
    - *Skill*: Usa la lógica definida en `agents/kit-instagram-web/`

## 📋 Reglas para el Agente

- **Prioriza Datos Reales**: Nunca inventes leads, teléfonos o URLs. Si no encuentras datos, informa al usuario.
- **Formato HTML**: Todas las auditorías y reportes deben generar un archivo HTML visual. Usa `open [archivo].html` después de generarlo.
- **Instagram first**: El usuario prioriza Instagram como método de contacto. Siempre que un lead no tenga Instagram, el pipeline lo busca automáticamente.
- **Configuración**: Si faltan API Keys, pídelas al usuario. El proyecto soporta archivos `.env.local`.
- **Estructura**:
    - `cli.py`: Entry point principal.
    - `extractor.py`: Búsqueda Text Search + Nearby Search + geocoding + grilla.
    - `instagram_search.py`: Búsqueda proactiva de Instagram vía API pública.
    - `pipeline.py`: Orquestador async.
    - `SKILL.md`: Definición formal de capacidades para Claude.

## 🚀 Comandos Rápidos

- Modo Interactivo: `python cli.py --interactive`
- Exploración por Cuadrantes: `python cli.py --explore`
- Prospección SEO: `python cli.py --limit 50 --goal seo --seo`
- Generar Reporte desde CSV: `python cli.py --from-csv [archivo].csv --html [reporte].html`
- Servir reporte con botones CRM: `python cli.py --serve`
- Enviar leads al CRM: `python cli.py --crm-send leads.csv`
