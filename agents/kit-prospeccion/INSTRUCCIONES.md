# Cómo usar este kit

## Requisitos

1. **Visual Studio Code** instalado (descarga en https://code.visualstudio.com)
2. **Extensión de Claude Code** instalada desde el marketplace de VS Code (busca "Claude Code" en extensiones)

## Paso 1 — Abrir este proyecto

1. Abre VS Code
2. Archivo → Abrir carpeta → selecciona esta carpeta (`kit-prospeccion`)
3. Abre Claude Code desde el panel lateral de VS Code

## Paso 2 — Pedir la búsqueda

Escribe algo como:

> "Busca 20 restaurantes en Barcelona que necesiten una web mejor"

> "Encuentra clínicas dentales en Madrid para ofrecerles SEO"

> "Quiero prospectar gimnasios en Valencia para venderles marketing digital"

Claude busca los negocios, analiza su presencia digital y genera el informe.

## Paso 3 — Ver el informe

Se abre un dashboard HTML con:
- Tabla de prospectos ordenada por oportunidad
- Análisis detallado de los mejores
- Mensajes de contacto personalizados listos para enviar
- Estadísticas del nicho
- Datos exportables (JSON)

## Extras

- Puedes dar URLs directamente: "Analiza estos 5 negocios: [urls]"
- Puedes pedir más detalle: "Profundiza en el prospecto #3"
- Puedes pedir otro formato: "Exporta los contactos para Google Sheets"

## Estructura

```
kit-prospeccion/
├── CLAUDE.md                             <- Claude lo lee automáticamente
├── INSTRUCCIONES.md                      <- Este archivo
└── .claude/
    └── skills/
        └── 06-prospeccion-firecrawl.md   <- La skill
```
