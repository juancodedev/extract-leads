---
name: auditoria-meta-ads
description: "Audita campañas de Meta Ads (Facebook/Instagram Ads) analizando los anuncios activos en la Biblioteca de Meta, las landing pages a las que llevan, y la coherencia entre ad y landing. Usa esta skill cuando el usuario quiera auditar sus anuncios, mejorar sus campañas de Facebook/Instagram Ads, analizar landing pages, o entender por qué sus ads no convierten. Triggers: 'audita mis Meta Ads', 'analiza mis anuncios de Facebook', 'por qué no convierten mis ads', 'auditoría de landing page', 'mejorar mis campañas', 'revisa mis Facebook Ads', 'analiza mis Instagram Ads', 'auditoría de anuncios'."
---

# Auditoría Meta Ads + Landing Pages

Analiza los anuncios activos de un negocio en la Biblioteca de Meta, las landing pages a las que llevan, y la coherencia entre ambos. Genera un informe con puntuación y correcciones para aumentar conversiones.

**Regla fundamental: análisis basado en datos reales.** Solo analiza anuncios que existan realmente en la Biblioteca de Meta. No inventes métricas de rendimiento que no puedes ver.

**Regla de formato: el resultado SIEMPRE es un archivo HTML.** No entregues el análisis como texto en el chat. Usa la herramienta Write para guardar el archivo `auditoria-meta-ads-[nombre].html` y luego ábrelo con `open [archivo]`. El HTML es el único entregable válido.

---

## Paso 1 — Recoger información

Pregunta al usuario:

- **Nombre de su página de Facebook o negocio** — para buscar en la Biblioteca de Ads
- **URL de la landing page principal** (si tiene)
- **¿Qué vende?** — producto, servicio, lead magnet, curso...
- **¿A qué precio?** — o si es captación de leads sin venta directa
- **¿Tiene datos de rendimiento?** — CTR, CPC, tasa de conversión, ROAS (opcional, si los tiene es oro)
- **¿Quién es su público objetivo?**

---

## Paso 2 — Extraer anuncios de la Biblioteca de Meta

### 2A. Buscar anuncios activos

Usa WebFetch o Playwright para acceder a la Biblioteca de Anuncios de Meta:

```
https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&q=[nombre del negocio]
```

También busca con WebSearch:
- `"[nombre negocio]" site:facebook.com/ads/library`
- `"[nombre negocio]" facebook ads library`

### 2B. Lo que extraer de cada anuncio

Para cada anuncio activo encontrado:
- **Creatividad**: ¿imagen, vídeo o carrusel?
- **Copy del anuncio**: texto principal, headline, descripción
- **CTA del anuncio**: qué botón usa (Más información, Comprar, Registrarse...)
- **URL de destino**: ¿a dónde lleva? ¿Landing específica o home genérica?
- **Fecha de inicio**: desde cuándo está activo (un ad activo mucho tiempo = probablemente rentable)
- **Plataformas**: Facebook, Instagram, Audience Network, Messenger
- **Variantes**: ¿tiene varias versiones del mismo anuncio? (A/B testing)

### 2C. Si no encuentra anuncios

Si el negocio no tiene anuncios activos:
- Informar al usuario
- Ofrecer auditar solo la landing page
- Sugerir qué tipo de anuncios debería crear según su negocio y público

---

## Paso 3 — Auditar los anuncios

Para cada anuncio encontrado, analiza:

### Creatividad
- **¿Capta la atención en los primeros 3 segundos?** — en Meta Ads compites con el scroll infinito
- **¿Se entiende la oferta sin leer el texto?** — muchas personas no leen, solo ven la imagen/vídeo
- **¿Tiene texto dentro de la imagen?** — Meta penaliza imágenes con más del 20% de texto
- **¿Es genérica o específica?** — fotos de stock vs fotos reales del producto/servicio
- **¿Muestra el resultado o el proceso?** — la gente compra resultados

### Copy del anuncio
- **Primera línea** — ¿engancha? ¿Tiene hook? La primera línea es lo que se ve antes de "Ver más"
- **¿Habla del beneficio o de la característica?** — "Pierde 5kg en 30 días" > "Programa nutricional avanzado"
- **¿Incluye prueba social?** — números, resultados, testimonios en el copy
- **¿Tiene CTA claro en el texto?** — además del botón
- **¿Usa emojis de forma estratégica o abusiva?**
- **Longitud** — ¿es adecuada para el tipo de oferta? (tráfico frío necesita más copy, retargeting menos)

### Estructura de campaña (si se puede inferir)
- **¿Cuántos anuncios activos tiene?** — pocos puede ser peligroso (fatiga), muchos puede ser desenfocado
- **¿Hay variantes?** — señal de que hace testing (bueno)
- **¿Los mensajes son consistentes?** — o cada anuncio dice algo distinto
- **¿Mezcla formatos?** — imagen + vídeo + carrusel = buena práctica

### Comentarios en los anuncios

Si puedes acceder a los comentarios de los anuncios (vía Playwright navegando al ad en Facebook), analízalos:

- **Objeciones reales** — ¿la gente pregunta sobre el precio, la garantía, los plazos? Esas son las objeciones que la landing debería responder
- **Quejas** — ¿hay quejas recurrentes? ¿Sobre qué?
- **Preguntas frecuentes** — ¿preguntan siempre lo mismo? Señal de que la info no está clara en el ad ni en la landing
- **Sentimiento general** — ¿positivo, negativo, escéptico?
- **¿Responde el negocio a los comentarios?** — no responder es perder ventas en público

Los comentarios son la investigación de mercado más honesta que existe — la gente dice exactamente lo que piensa.

---

## Paso 3B — Analizar ads de competidores

Si el usuario proporcionó competidores (o puedes inferirlos del sector):

1. Busca sus anuncios en la Biblioteca de Meta con la misma técnica
2. Para cada competidor analiza:
   - **¿Cuántos ads activos tienen?** — más ads = más inversión = más serio
   - **¿Qué mensajes usan?** — ¿ángulos diferentes al auditado?
   - **¿Qué ofertas hacen?** — precios, bonos, garantías
   - **¿Qué formatos usan?** — vídeo, imagen, carrusel
   - **¿Desde cuándo están activos sus mejores ads?** — ads con meses activos = probablemente rentables (referencia para el auditado)
   - **¿A dónde llevan?** — ¿landing específica o home?

3. Comparativa directa:
   - ¿El auditado tiene más o menos ads que la competencia?
   - ¿Sus mensajes son más fuertes o más débiles?
   - ¿Los competidores están usando ángulos que el auditado no ha probado?
   - **Oportunidades**: mensajes, ofertas o formatos que la competencia usa con éxito y el auditado no

---

## Paso 3C — Benchmarks del sector

Contextualiza los datos con benchmarks medios. Busca con WebSearch datos actualizados de benchmarks de Meta Ads para el sector del usuario:

- `"Meta Ads benchmarks [sector] 2025 2026 CTR CPC"`
- `"Facebook Ads average CTR [industry]"`

**Benchmarks de referencia generales (si no encuentras del sector):**

| Métrica | Media general | Bueno | Excelente |
|---------|-------------|-------|-----------|
| CTR (link) | 1.5-2% | 2-3% | >3% |
| CPC | 0.50-1.50€ | <0.50€ | <0.30€ |
| CPM | 8-15€ | <8€ | <5€ |
| Tasa de conversión landing | 2-5% | 5-10% | >10% |
| ROAS | 2-3x | 3-5x | >5x |

Si el usuario proporcionó sus datos de rendimiento, compáralos con los benchmarks y resalta:
- Métricas que están por debajo de la media (problemas)
- Métricas que están por encima (fortalezas)
- Dónde tiene más margen de mejora

Si no tiene datos de rendimiento, usa los benchmarks como referencia para estimar qué debería esperar.

---

## Paso 4 — Auditar la landing page

Para cada URL de destino de los anuncios, analiza con WebFetch:

### Above the fold (lo primero que se ve)
- **¿El headline coincide con el mensaje del anuncio?** — el "message match" es crítico
- **¿Hay CTA visible sin hacer scroll?**
- **¿La propuesta de valor es clara en 5 segundos?**
- **¿Hay imagen/vídeo que refuerce el mensaje?**

### Copy de la landing
- **¿Habla de beneficios o de características?**
- **¿Usa el lenguaje del cliente?** — no jerga técnica
- **¿Aborda objeciones?** — "¿Es para mí?", "¿Funciona?", "¿Y si no me gusta?"
- **¿Sigue una estructura persuasiva?** — AIDA (Atención, Interés, Deseo, Acción) o PAS (Problema, Agitación, Solución)
- **¿La longitud es adecuada?** — oferta cara = más copy, lead magnet gratis = menos

### CTA y conversión
- **¿Cuántos CTAs hay?** — ideal: 1 principal repetido 2-3 veces
- **¿El texto del botón es específico?** — "Quiero mi plan gratis" > "Enviar"
- **¿El botón contrasta visualmente?**
- **¿Hay urgencia/escasez?** — plazas limitadas, countdown, oferta temporal

### Social proof
- **¿Hay testimonios?** — ¿con nombre, foto, resultado concreto?
- **¿Hay números de prueba social?** — "X clientes", "X resultados"
- **¿Hay logos de clientes/medios/certificaciones?**
- **¿Hay garantía?**

### Formulario (si es captación de leads)
- **¿Cuántos campos?** — menos = más conversión en tráfico frío
- **¿Pide solo lo necesario?**
- **¿El botón tiene texto de acción?**

### Técnico
- **¿Tiene pixel de Facebook?** — buscar `fbq(` o `facebook.com/tr` en el código
- **¿Tiene eventos de conversión?** — buscar `fbq('track',`
- **¿Es responsive?**
- **¿Carga rápido?** — tiempo de respuesta con curl
- **¿HTTPS?**
- **¿Tiene Google Analytics u otro tracking?**

---

## Paso 5 — Coherencia Ad ↔ Landing

Este es el análisis más valioso. Compara cada anuncio con su landing de destino:

- **Message match** — ¿el headline del ad coincide con el headline de la landing? Si el ad dice "Pierde 5kg en 30 días" y la landing dice "Bienvenido a nuestra web de nutrición", hay un desconexión que mata la conversión.
- **Oferta match** — ¿la oferta es exactamente la misma? ¿El precio cuadra?
- **Visual match** — ¿los colores, estilo y tono son coherentes?
- **CTA match** — ¿lo que promete el botón del ad es lo que encuentra en la landing?
- **Público match** — ¿el tono del ad habla al mismo público que la landing?

Puntúa el message match de 0-100. Cualquier cosa por debajo de 70 es un problema serio.

---

## Paso 6 — Generar el informe HTML (OBLIGATORIO)

**Este paso no es opcional.** Toda auditoría termina con un archivo HTML guardado con Write. Nunca respondas con el análisis solo en texto.

Dashboard visual. Libertad creativa total en diseño.

### Contenido obligatorio

1. **Puntuación global** (0-100) con veredicto:
   - 80-100: "Campaña bien optimizada — ajustes menores"
   - 60-79: "Campaña funcional — hay margen de mejora significativo"
   - 40-59: "Campaña con problemas — correcciones necesarias"
   - 0-39: "Campaña no optimizada — rediseño recomendado"

2. **Resumen de anuncios encontrados** — Cuántos ads activos, desde cuándo, qué formatos, qué mensajes. Vista rápida de todos los anuncios.

3. **Análisis ad por ad** — Para cada anuncio:
   - Copy analizado con hallazgos
   - Puntuación de la creatividad
   - URL de destino y su análisis
   - Message match score con la landing

4. **Análisis de la landing** — Los puntos auditados con:
   - Puntuación por área
   - Lo que está bien / lo que falla
   - Correcciones con código exacto o copy alternativo

5. **Incoherencias Ad ↔ Landing** — Sección destacada con cada desconexión encontrada y cómo resolverla

6. **Reescrituras sugeridas** — Para los elementos que fallan:
   - 3 headlines alternativos para la landing
   - CTA alternativo
   - Copy mejorado para secciones débiles
   - Hook alternativo para el primer línea del ad

7. **Checklist de implementación** — Ordenada por impacto:
   - Cada corrección con impacto estimado (alto/medio/bajo) y tiempo
   - Las de mayor impacto primero

8. **Benchmarks** — Tabla comparativa de los datos del usuario (si los proporcionó) vs media del sector. Resaltar dónde está por debajo y por encima.

9. **Análisis de competidores** (si aplica) — Comparativa de ads: cuántos tienen, qué mensajes usan, qué ofertas, qué hacen que el auditado no.

10. **Insights de los comentarios** (si se pudieron extraer) — Objeciones reales de la audiencia, preguntas frecuentes, sentimiento general. Estas son recomendaciones directas para mejorar tanto los ads como la landing.

11. **Pack de nuevos anuncios listos para lanzar** — Genera 3-5 anuncios nuevos completos, no solo ideas:

   Para cada anuncio nuevo incluye:
   - **Hook** (primera línea que engancha)
   - **Copy completo** del anuncio (texto principal)
   - **Headline** (el título bajo la imagen)
   - **Descripción**
   - **CTA recomendado** (botón)
   - **Ángulo/enfoque** (por qué este ángulo puede funcionar)
   - **Formato sugerido** (imagen, vídeo, carrusel)
   - **Briefing del creativo** (qué debería mostrar la imagen/vídeo)

   Usa ángulos diferentes para cada uno:
   - Ángulo de resultado ("Conseguí X en Y tiempo")
   - Ángulo de problema ("¿Cansado de X?")
   - Ángulo de prueba social ("Más de X personas ya...")
   - Ángulo de curiosidad ("El método que nadie te cuenta")
   - Ángulo de contraste ("Antes hacía X, ahora hago Y")

   Los copies deben estar escritos para el público objetivo del usuario, con su tono y su lenguaje. Listos para copiar y pegar en el Ads Manager.

### Requisitos del dashboard
- Responsive
- Autocontenido
- Imprimible
- Que incluya los textos de los anuncios reales dentro del informe

---

## Paso 7 — Guardar y presentar

- Guarda como `auditoria-meta-ads-[nombre].html`
- Abre en el navegador

Presenta:
1. Cuántos anuncios analizados
2. Puntuación global
3. El problema principal (la mayor fuga de conversión)
4. Top 3 correcciones con mayor impacto
5. Pregunta si quiere que reescriba copies, headlines o CTAs

No muestres precios sugeridos ni consejos de venta.
