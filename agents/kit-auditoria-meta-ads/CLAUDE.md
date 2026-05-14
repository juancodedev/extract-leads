# Auditoría Meta Ads + Landing Pages

Este proyecto audita campañas de Facebook/Instagram Ads: busca los anuncios activos en la Biblioteca de Meta, analiza las landing pages a las que llevan, y detecta la coherencia entre ambos.

## Comportamiento al iniciar

Cuando el usuario abra esta carpeta y escriba cualquier cosa, responde:

> **Bienvenido a la auditoría de Meta Ads**
>
> Voy a analizar tus anuncios de Facebook/Instagram y las landing pages a las que llevan. Busco incoherencias, problemas de copy, oportunidades de mejora y te doy correcciones concretas.
>
> Necesito:
> 1. **Nombre de tu página de Facebook o negocio** (para buscar tus anuncios en la Biblioteca de Meta)
> 2. **URL de tu landing page** (si la tienes)
> 3. **¿Qué vendes y a quién?**
>
> ¿Empezamos?

Después usa la skill `auditoria-meta-ads` automáticamente.

## Qué analiza

- **Anuncios activos**: creatividad, copy, hooks, CTAs, formatos, tiempo activos
- **Landing pages**: headline, propuesta de valor, social proof, formulario, estructura persuasiva
- **Coherencia Ad ↔ Landing**: message match, oferta, tono, visual
- **Pixel y tracking**: si tiene Facebook Pixel, eventos de conversión, Analytics
- **Copy**: headlines, CTAs, si habla de beneficios o características, objeciones

## Formato de salida — OBLIGATORIO

**SIEMPRE genera la auditoría como un archivo HTML.** Sin excepciones.

- Nombre del archivo: `auditoria-meta-ads-[nombre-negocio].html`
- Guárdalo con la herramienta Write
- Ábrelo en el navegador con `open [archivo]`
- No entregues el análisis solo como texto en el chat — el resultado final es el HTML

## No necesita nada instalado

Claude usa WebSearch, WebFetch y Playwright (si disponible) para acceder a la Biblioteca de Meta y analizar las landings.
