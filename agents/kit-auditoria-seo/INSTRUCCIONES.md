# Cómo usar este kit

## Requisitos

1. **Visual Studio Code** instalado (descarga en https://code.visualstudio.com)
2. **Extensión de Claude Code** instalada desde el marketplace de VS Code (busca "Claude Code" en extensiones)

No necesita Python, Node.js ni nada extra.

## Paso 1 — Abrir este proyecto

1. Abre VS Code
2. Archivo → Abrir carpeta → selecciona esta carpeta (`kit-auditoria-seo`)
3. Abre Claude Code desde el panel lateral de VS Code

## Paso 2 — Dar la URL

Escribe algo como:

> Audita el SEO de https://midominio.com

Claude analiza automáticamente:
- Meta tags (title, description, canonical...)
- Headings (h1-h6)
- Imágenes (alt, lazy loading, formatos)
- Enlaces (rotos, noopener, anclas)
- Open Graph y Twitter Cards
- Schema / JSON-LD
- Técnico (HTTPS, robots.txt, sitemap, velocidad)
- Contenido (palabras, ratio texto/HTML)

## Paso 3 — Ver el informe

Claude genera un dashboard HTML y lo abre en tu navegador con:
- Puntuación global (0-100)
- Top 5 correcciones con código exacto para aplicar
- Desglose de las 8 categorías
- Tabla de detalle técnico completo

## Paso 4 — Aplicar correcciones (opcional)

Si tienes el código de la web accesible, dile a Claude:

> Aplica las correcciones en mi código

Y las implementará directamente.

## Extras

- Puedes auditar competidores: "Audita también https://competidor.com para comparar"
- Puedes indicar una keyword: "Quiero posicionar por 'agencia de marketing digital'"

## Estructura

```
kit-auditoria-seo/
├── CLAUDE.md                      <- Claude lo lee automáticamente
├── INSTRUCCIONES.md               <- Este archivo
└── .claude/
    └── skills/
        └── 03-auditoria-seo.md    <- La skill
```
