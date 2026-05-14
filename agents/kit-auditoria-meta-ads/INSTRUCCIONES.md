# Cómo usar este kit

## Requisitos

1. **Visual Studio Code** instalado (descarga en https://code.visualstudio.com)
2. **Extensión de Claude Code** instalada desde el marketplace de VS Code (busca "Claude Code" en extensiones)

## Paso 1 — Abrir este proyecto

1. Abre VS Code
2. Archivo → Abrir carpeta → selecciona esta carpeta (`kit-auditoria-meta-ads`)
3. Abre Claude Code desde el panel lateral de VS Code

## Paso 2 — Pedir la auditoría

Escribe algo como:

> "Audita los Meta Ads de mi negocio [nombre]. Mi landing es https://midominio.com/oferta"

> "Analiza mis anuncios de Facebook, mi página se llama [nombre]"

> "¿Por qué no convierten mis Instagram Ads? Mi landing es [url]"

Claude busca tus anuncios en la Biblioteca de Meta, analiza las landing pages y genera el informe.

## Paso 3 — Ver el informe

Se abre un dashboard HTML con:
- Todos tus anuncios activos analizados
- Análisis completo de la landing page
- Message match (coherencia anuncio ↔ landing)
- Reescrituras sugeridas de headlines y CTAs
- Checklist de correcciones ordenadas por impacto

## Extras

- Si tienes datos de rendimiento (CTR, CPC, tasa de conversión), dáselos a Claude para un análisis más profundo
- Puedes pedir que reescriba copies: "Reescribe el headline de mi landing"
- Puedes pedir nuevos ángulos: "Dame 5 hooks diferentes para probar en mis ads"

## Estructura

```
kit-auditoria-meta-ads/
├── CLAUDE.md                              <- Claude lo lee automáticamente
├── INSTRUCCIONES.md                       <- Este archivo
└── .claude/
    └── skills/
        └── 08-auditoria-meta-ads.md       <- La skill
```
