# Cómo usar este kit

## Requisitos

1. **Visual Studio Code** instalado (descarga en https://code.visualstudio.com)
2. **Extensión de Claude Code** instalada desde el marketplace de VS Code (busca "Claude Code" en extensiones)

## Paso 1 — Abrir este proyecto

1. Abre VS Code
2. Archivo → Abrir carpeta → selecciona esta carpeta (`kit-auditoria-negocio`)
3. Abre Claude Code desde el panel lateral de VS Code

## Paso 2 — Pedir la auditoría

Escribe algo como:

> "Audita mi negocio digital. Mi web es https://midominio.com, estoy en Instagram como @mihandle y vendo consultoría de marketing"

Claude investigará tu web, tus redes, tu oferta y todo lo que pueda encontrar online. Te hará preguntas complementarias si necesita más contexto.

## Paso 3 — Ver el informe

Se abre un dashboard HTML con:
- Puntuación global y por área
- Incoherencias y errores detectados (la parte más valiosa)
- Mapa del embudo de ventas actual
- Plan de acción priorizado
- Quick wins para hacer esta semana
- Comparativa con competencia (si la proporcionaste)

## Extras

- Puedes dar competidores: "Compárame con https://competidor.com"
- Puedes pedir foco: "Céntrate en mi embudo de ventas"
- Puedes pedir que aplique mejoras: "Corrige lo que puedas en mi web"

## Estructura

```
kit-auditoria-negocio/
├── CLAUDE.md                                    <- Claude lo lee automáticamente
├── INSTRUCCIONES.md                             <- Este archivo
└── .claude/
    └── skills/
        └── 07-auditoria-negocio-digital.md      <- La skill
```
