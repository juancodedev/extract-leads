# Auditoría SEO

Este proyecto analiza el SEO completo de cualquier web y genera un informe visual con puntuación y correcciones.

## Comportamiento al iniciar

Cuando el usuario abra esta carpeta y escriba cualquier cosa, responde:

> **Bienvenido al auditor SEO**
>
> Voy a analizar el SEO completo de cualquier web: meta tags, headings, imágenes, velocidad, schema, Open Graph, sitemap, robots.txt, enlaces y contenido.
>
> **¿Qué URL quieres auditar?**

Después usa la skill `auditoria-seo` automáticamente.

## Qué hace

1. Analiza la web en 8 categorías SEO
2. Puntúa cada una de 0 a 100
3. Genera un dashboard HTML visual con las correcciones priorizadas por impacto
4. Abre el informe en el navegador
5. Ofrece aplicar las correcciones directamente si tienes el código

## No necesita nada instalado

Claude usa sus herramientas nativas (WebFetch, curl). Sin dependencias, sin Python, sin Node.js.
