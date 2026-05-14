# Lead Extractor & Business Auditor — Claude Guide

Este proyecto está optimizado para ser usado por Claude Code. Como agente, tienes acceso a herramientas de extracción de leads, auditoría SEO, auditoría de anuncios y generación de prototipos web.

## 🛠 Skills Disponibles

Puedes activar estas capacidades directamente:

1.  **Prospección Inteligente**: Busca negocios reales, analízalos y genera un informe de oportunidades.
    - *Ejemplo*: "Busca 20 barberías en Santiago para venderles web"
    - *Comando*: `python pipeline.py --limit 20 --goal web`

2.  **Auditoría SEO Técnica**: Realiza un análisis profundo de cualquier sitio web.
    - *Ejemplo*: "Audita el SEO de https://ejemplo.com"
    - *Skill*: Usa la lógica definida en `agents/kit-auditoria-seo/`

3.  **Auditoría de Meta Ads**: Analiza anuncios activos y su coherencia con la landing page.
    - *Ejemplo*: "Analiza los anuncios de [Negocio] y su web [URL]"
    - *Skill*: Usa la lógica definida en `agents/kit-auditoria-meta-ads/`

4.  **Instagram → Web**: Convierte un perfil de Instagram en un prototipo de sitio web profesional.
    - *Ejemplo*: "Convierte @usuario en una web de marca personal"
    - *Skill*: Usa la lógica definida en `agents/kit-instagram-web/`

## 📋 Reglas para el Agente

- **Prioriza Datos Reales**: Nunca inventes leads, teléfonos o URLs. Si no encuentras datos, informa al usuario.
- **Formato HTML**: Todas las auditorías y reportes deben generar un archivo HTML visual. Usa `open [archivo].html` después de generarlo.
- **Configuración**: Si faltan API Keys, pídelas al usuario. El proyecto soporta archivos `.env.local`.
- **Estructura**:
    - `pipeline.py`: Orquestador principal.
    - `analyzer.py`: Análisis técnico de webs.
    - `SKILL.md`: Definición formal de capacidades para Claude.

## 🚀 Comandos Rápidos

- Modo Interactivo: `python pipeline.py --interactive`
- Prospección SEO: `python pipeline.py --limit 50 --goal seo --seo`
- Generar Reporte desde CSV: `python pipeline.py --from-csv [archivo].csv --html [reporte].html`
