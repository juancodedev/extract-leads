---
name: auditoria-negocio
description: "Audita la presencia digital completa de un negocio: web, redes sociales, lo que vende, precios, ofertas, cómo vende, embudo de ventas, reputación y coherencia de marca. Detecta incoherencias, errores y mejoras. Usa esta skill cuando el usuario quiera auditar un negocio, analizar su presencia online, revisar cómo vende, detectar errores en su estrategia digital, o mejorar su negocio digital. Triggers: 'audita mi negocio', 'análisis digital', 'qué tal está mi presencia online', 'auditoría de mi marca', 'cómo mejorar mi negocio digital', 'revisa mi negocio', 'qué estoy haciendo mal', 'analiza cómo vendo'."
---

# Auditoría de Negocio Digital

Le das la información de un negocio y Claude audita TODO: web, redes sociales, lo que vende, cómo lo vende, precios, ofertas, embudo de ventas, coherencia de marca, reputación y competencia. Genera un informe ejecutivo con errores, incoherencias y plan de acción.

**Regla fundamental: análisis honesto y basado en datos reales.** No suavices los problemas ni exageres los aciertos. El valor de una auditoría está en la verdad.

---

## Paso 1 — Recoger toda la información del negocio

Pregunta al usuario todo lo necesario. Agrupa en 2 mensajes:

### Bloque 1 — Lo básico

- **URL de la web** (si tiene)
- **Redes sociales** — Instagram, TikTok, YouTube, LinkedIn, Facebook, Twitter/X (las que tenga, con @ o URLs)
- **¿Qué vende exactamente?** — productos, servicios, cursos, consultoría, etc.
- **¿A qué precio?** — rangos, tarifas, si tiene ofertas activas
- **¿Quién es su cliente ideal?** — a quién se dirige

### Bloque 2 — Contexto estratégico

- **¿Cuál es su objetivo principal ahora?** — más ventas, más leads, más visibilidad, lanzar algo nuevo...
- **¿Tiene competidores directos que conozca?** — 1-2 URLs o nombres para comparar
- **¿Qué canales usa para vender?** — web directa, redes sociales, email marketing, ads, boca a boca...
- **¿Tiene algo que crea que no funciona?** — a veces el usuario ya sabe dónde le duele

Si el usuario no quiere dar mucho contexto, trabaja con lo que te dé. Puedes investigar el resto por tu cuenta.

---

## Paso 2 — Investigar y auditar

Usa WebSearch, WebFetch y Bash para recopilar toda la info posible. Investiga a fondo antes de opinar.

### 2A. Web (si tiene)

Con WebFetch analiza:
- **Primera impresión** — ¿se entiende qué vende en los primeros 5 segundos? ¿El h1 y hero son claros?
- **Propuesta de valor** — ¿está diferenciada o es genérica ("los mejores", "calidad y servicio")?
- **CTA (llamadas a la acción)** — ¿hay botones claros? ¿Hacia dónde llevan? ¿Cuántos clicks hasta la compra/contacto?
- **Precios** — ¿son visibles o hay que pedir presupuesto? ¿Las ofertas están claras? ¿Hay incoherencias entre precios de la web y redes?
- **Testimonios / Social proof** — ¿tiene pruebas de que funciona?
- **Lead magnet / Captación** — ¿captura emails? ¿Tiene formularios? ¿Pop-ups?
- **Email marketing** — buscar en el código: Mailchimp, ConvertKit, ActiveCampaign, Brevo, etc.
- **Chat / WhatsApp** — ¿tiene canal de contacto rápido?
- **Velocidad y técnico** — tiempo de respuesta, HTTPS, responsive

### 2B. Redes sociales

Para cada red que tenga, usa Playwright (si disponible) o WebFetch + WebSearch:

- **Bio** — ¿es clara? ¿Dice qué hace y para quién? ¿Tiene CTA?
- **Link en bio** — ¿lleva a la oferta correcta o a una home genérica?
- **Contenido** — ¿qué tipo de posts hace? ¿Educativo, entretenimiento, venta directa?
- **Frecuencia** — ¿cada cuánto publica? ¿Hay gaps largos sin publicar?
- **Coherencia visual** — ¿los colores, tono y estilo son consistentes entre redes y web?
- **Engagement** — ¿tiene interacción real o solo publica y nadie responde?
- **Seguidores vs interacción** — ratio sano o seguidores inflados con 0 engagement

### 2C. Lo que vende y cómo lo vende

Esto es la parte más importante. Analiza:

- **Oferta** — ¿qué vende exactamente? ¿Está bien definido o es confuso?
- **Precio** — ¿es coherente con el posicionamiento? ¿Se posiciona premium pero el precio es bajo? ¿O al revés?
- **Ofertas activas** — ¿tiene descuentos, bonos, paquetes? ¿Tienen sentido o son confusas?
- **Página de ventas** — ¿hay una página específica para cada producto/servicio o está todo mezclado?
- **Proceso de compra** — ¿cuántos pasos del "quiero esto" al "lo he comprado"? ¿Hay fricción?
- **Incoherencias** — ¿dice una cosa en Instagram y otra en la web? ¿Los precios no cuadran? ¿La oferta de Stories es diferente a la de la web?

### 2D. Anuncios (Meta Ads Library)

Busca si el negocio tiene anuncios activos en la Biblioteca de Anuncios de Meta:

1. Usa WebFetch o Playwright para acceder a `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&q=[nombre del negocio]`
2. También busca con WebSearch: `"[nombre negocio]" site:facebook.com/ads/library`

Si tiene anuncios activos, analiza:
- **¿Cuántos anuncios tiene activos?**
- **¿Desde cuándo están corriendo?** — un anuncio activo mucho tiempo suele ser rentable
- **¿Qué tipo de creativos usa?** — imagen, vídeo, carrusel
- **¿Qué mensaje/copy usan los anuncios?** — ¿es coherente con lo que dice en la web y redes?
- **¿Hacia dónde llevan?** — ¿a la home genérica o a una landing específica?
- **¿El CTA del anuncio es claro?**
- **Incoherencias ads vs web** — ¿el anuncio promete algo que la web no refleja? ¿Los precios del ad no cuadran con los de la web?

Si NO tiene anuncios: registrarlo como observación (no necesariamente es un error — depende del tipo de negocio).

### 2E. Análisis del Copy

Analiza el lenguaje y los textos que usa el negocio en todos sus canales:

- **¿Habla para su cliente ideal o para sí mismo?** — muchos negocios hablan de lo que hacen en vez de lo que el cliente consigue
- **¿Usa lenguaje que su audiencia entiende?** — tecnicismos innecesarios, jerga del sector que el cliente no conoce
- **¿Los títulos son claros y atractivos?** — o son genéricos tipo "Bienvenido a nuestra web"
- **¿Tiene un mensaje diferenciador?** — ¿por qué elegirle a él y no a otro? ¿Lo comunica?
- **¿El tono es coherente entre canales?** — ¿mismo tono en web, Instagram, ads, emails?
- **¿Usa prueba social en el copy?** — números, resultados, testimonios integrados en el texto
- **¿Responde objeciones?** — ¿anticipa las dudas del cliente antes de que las piense?
- **¿Los CTAs son específicos o genéricos?** — "Reserva tu plaza" es mejor que "Enviar", "Empieza tu transformación" es mejor que "Más información"

Compara el copy de la web vs redes vs ads (si tiene). Las incoherencias de tono o mensaje son un hallazgo importante.

### 2F. Customer Journey completo

No solo el embudo de venta — mapea todo el recorrido del cliente, incluido lo que pasa DESPUÉS de comprar:

**PRE-VENTA:**
```
Descubrimiento → Primera impresión → Investigación → Consideración → Decisión
```
- ¿Cómo te descubren? (redes, Google, ads, referidos)
- ¿Qué ven primero? ¿Engancha?
- ¿Pueden investigar fácilmente? (precios, testimonios, portfolio)
- ¿Hay algo que resuelva objeciones? (FAQ, garantías, prueba gratis)
- ¿El proceso de compra/contacto es sencillo?

**POST-VENTA:**
- ¿Hay seguimiento después de la compra? (email de bienvenida, onboarding)
- ¿Tiene sistema de upsell/cross-sell? (otros productos/servicios relacionados)
- ¿Pide reseñas o referidos?
- ¿Tiene programa de fidelización o recurrencia?
- ¿Mantiene comunicación con clientes existentes? (newsletter, comunidad)

Los negocios que solo se centran en captar y no en retener pierden mucho dinero. Detectar si tiene post-venta es un hallazgo muy valioso.

### 2G. Google Maps / Google Business

Busca la ficha de Google Business del negocio:

1. WebSearch: `"[nombre negocio]" "[ciudad]" google maps`
2. O directamente en la web, buscar si tiene link a Google Maps

Si tiene ficha, analiza:
- **¿Está reclamada y verificada?**
- **¿Tiene fotos?** — ¿cuántas? ¿Son profesionales o parecen hechas con el móvil de hace 5 años?
- **¿Tiene descripción del negocio?**
- **¿Horarios actualizados?**
- **Puntuación media** — ¿cuántas estrellas? ¿Cuántas reseñas?
- **¿Responde a las reseñas?** — tanto positivas como negativas. No responder reseñas negativas es un error grave.
- **¿Las reseñas mencionan problemas recurrentes?** — si 3 reseñas hablan de lo mismo, es un patrón real
- **¿La info de Google Business coincide con la web?** — horarios, teléfono, dirección, servicios

Si NO tiene ficha de Google Business y es un negocio local: es un error grave y un quick win inmediato.

### 2H. Competencia (análisis profundo)

Si el usuario dio competidores, haz un análisis serio, no superficial:

**Comparar oferta vs oferta:**
- ¿Qué venden los competidores? ¿A qué precio?
- ¿Dónde está posicionado el auditado respecto a sus competidores? (más caro, más barato, similar)
- ¿La diferencia de precio se justifica con la diferencia de valor?

**Comparar presencia digital:**
- Web: ¿cuál se ve más profesional? ¿Cuál convierte mejor?
- Redes: ¿quién tiene más engagement real (no solo seguidores)?
- SEO: ¿quién aparece primero en Google para las keywords del sector?
- Ads: ¿los competidores hacen publicidad? ¿Con qué mensajes?

**Comparar posicionamiento:**
- ¿Hablan al mismo público o a segmentos diferentes?
- ¿Hay un hueco que nadie está ocupando?
- ¿El auditado tiene algo que los competidores no? ¿Lo comunica?

**Oportunidades de diferenciación:**
- Lista concreta de cosas que el auditado podría hacer diferente
- No genéricas ("ser más innovador") sino específicas ("ofrecer garantía de devolución que ningún competidor ofrece")

---

## Paso 3 — Detectar incoherencias y errores

Esta es la parte que más valor aporta. Busca activamente:

### Incoherencias comunes

- **Precio vs posicionamiento** — se vende como premium pero los precios son de gama baja (o al revés)
- **Mensaje vs audiencia** — habla como si vendiera a corporaciones pero su cliente es autónomo
- **Web vs redes** — tono formal en la web pero informal en Instagram (o al revés sin sentido)
- **Promesa vs entrega** — promete resultados en 30 días pero no tiene testimonios que lo demuestren
- **Ofertas contradictorias** — descuento del 50% en Instagram pero precio completo en la web
- **Bio vs realidad** — dice "experto en X" pero su contenido habla de Y
- **Muchos servicios sin foco** — hace de todo para todos (señal de que no tiene posicionamiento)

### Errores comunes

- No tener un CTA claro en ningún sitio
- No capturar emails (sin lead magnet, sin formularios)
- Redes sociales abandonadas (peor que no tenerlas)
- Blog muerto con último post de hace 1 año
- Precios ocultos que generan desconfianza
- Página de ventas que no responde objeciones
- Demasiados pasos para comprar/contactar
- Cero testimonios o social proof

---

## Paso 4 — Generar el informe HTML

Dashboard ejecutivo visual. Libertad creativa total en diseño.

### Contenido obligatorio

1. **Puntuación global** (0-100) con desglose visual por área:
   - Web y UX
   - SEO (versión resumida)
   - Redes Sociales
   - Anuncios (Meta Ads)
   - Copy y Comunicación
   - Oferta y Precios
   - Customer Journey (pre y post-venta)
   - Google Business / Maps
   - Contenido
   - Reputación
   - Coherencia de Marca
   - Competencia (si aplica)

2. **Resumen ejecutivo** — 3 párrafos máximo:
   - Estado actual (dónde está)
   - El problema principal (por qué no crece)
   - La oportunidad (qué puede ganar si lo arregla)

3. **Incoherencias y errores detectados** — Sección destacada con:
   - Cada incoherencia explicada de forma clara
   - Por qué es un problema
   - Cómo corregirla
   - Prioridad (alta/media/baja)

4. **Mapa del Customer Journey completo** — Diagrama visual del recorrido COMPLETO:
   ```
   [Descubrimiento] → [Primera visita] → [Interés] → [Conversión] → [Post-venta] → [Retención/Referidos]
   ```
   Con indicación clara de dónde se pierden los clientes y qué fases no existen.

5. **Análisis de Ads** — Si tiene anuncios en Meta: cuántos, desde cuándo, qué dicen, coherencia con la web. Si no tiene: indicar si debería tenerlos.

6. **Análisis del Copy** — Hallazgos sobre el lenguaje: ¿habla para el cliente o para sí mismo? ¿CTAs genéricos? ¿Tono coherente entre canales? Ejemplos concretos de mejoras con antes/después.

7. **Google Business** — Estado de la ficha, reseñas, fotos, si responde a reseñas negativas.

5. **Desglose por área** — Cada pilar con:
   - Puntuación
   - Lo que está bien
   - Lo que está mal
   - Acciones concretas

6. **Plan de acción priorizado** — Tabla con:
   | Prioridad | Acción | Impacto | Esfuerzo | Área |

7. **Quick wins** — Las 3-5 cosas que puede hacer esta semana:
   - Qué hacer (concreto)
   - Resultado esperado
   - Tiempo estimado

8. **Comparativa con competencia** (si aplica) — Tabla lado a lado

### Requisitos del dashboard

- Responsive
- Autocontenido (CSS y JS inline)
- Imprimible / exportable a PDF
- Navegación interna
- Tono profesional pero directo — que no parezca un informe de consultoría genérico

---

## Paso 5 — Guardar y presentar

- Guarda como `auditoria-negocio-[dominio].html`
- Abre automáticamente en el navegador

Presenta:
1. Puntuación global
2. El problema principal del negocio en una frase
3. Los 3 quick wins más urgentes
4. Pregunta si quiere profundizar en algún área o que aplique correcciones

No muestres precios sugeridos ni consejos de venta.
