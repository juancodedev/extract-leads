---
name: auditoria-seo
description: "Audita el SEO completo de cualquier web y genera un informe visual con puntuación y correcciones específicas. Usa esta skill cuando el usuario quiera analizar el SEO de una web, verificar su posicionamiento, revisar meta tags, analizar la estructura, o mejorar su visibilidad en Google. Triggers: 'audita el SEO', 'analiza mi web', 'revisa el posicionamiento', 'qué está mal en mi SEO', 'cómo mejorar mi web en Google', 'auditoría SEO', 'analiza esta URL', 'revisa mi página', 'SEO de mi web'."
---

# Auditoría SEO Completa

Le das una URL y Claude analiza todo: meta tags, headings, velocidad, schema, Open Graph, sitemap, robots.txt, imágenes, enlaces. Genera un dashboard HTML visual con puntuación global y correcciones priorizadas por impacto.

**Regla fundamental: solo reporta datos reales.** Cada hallazgo debe estar respaldado por lo que encontraste en la web. No inventes problemas ni infles la gravedad.

---

## Paso 1 — Obtener la URL y contexto

Pide al usuario la **URL completa** del sitio a auditar.

Pregunta también:
- **¿Es tu web o la de un competidor?** — cambia el tono del informe
- **¿Quieres que audite también algún competidor para comparar?** — si da 1-2 URLs más, incluye comparativa
- **¿Hay alguna keyword o búsqueda por la que quieras posicionar?** — si la da, evalúa la presencia de esa keyword en title, h1, contenido, meta description

Si el usuario no quiere dar más contexto y solo da la URL, empieza directamente con la auditoría.

---

## Paso 2 — Recopilar datos de la web

Usa las herramientas nativas de Claude Code para extraer todo. No necesitas instalar nada — WebFetch y Bash son suficientes.

### 2A. Página principal

Usa WebFetch para descargar y analizar la página. Extrae:
- HTML completo para analizar estructura
- Todos los meta tags
- Estructura de headings (h1-h6)
- Imágenes y sus atributos alt
- Enlaces internos y externos
- Schema / JSON-LD
- Open Graph y Twitter Cards

### 2B. Archivos técnicos

Verifica con WebFetch o curl:
- `[URL]/robots.txt` — ¿existe? ¿qué bloquea?
- `[URL]/sitemap.xml` — ¿existe? ¿está bien formado?
- `[URL]/favicon.ico` — ¿existe?

### 2C. Verificaciones técnicas

Con Bash (curl):
```bash
# Tiempo de respuesta y headers
curl -sI -o /dev/null -w "HTTP %{http_code} | Tiempo: %{time_total}s | Redirect: %{redirect_url}" [URL]

# Verificar HTTPS
curl -sI [URL] | head -5

# Verificar si hay redirección www vs no-www
curl -sI http://[dominio] 2>/dev/null | grep -i location
curl -sI https://www.[dominio] 2>/dev/null | grep -i location
```

### 2D. Verificación de enlaces (los primeros 15-20)

Verifica el status code de los enlaces internos más importantes para detectar enlaces rotos (404). No hagas más de 20 peticiones para no saturar el servidor.

### 2E. Páginas secundarias (opcional)

Si el usuario lo pide, audita también 2-3 páginas internas (about, servicios, blog) para tener una visión más completa.

---

## Paso 3 — Evaluar cada categoría

Puntúa cada categoría de 0 a 100. Sé justo y objetivo — no regales puntos pero tampoco penalices en exceso por cosas menores.

### Categorías y pesos

**1. Meta Tags (20%)**
- `<title>`: ¿existe? ¿longitud 50-60 chars? ¿descriptivo y con keyword?
- `<meta description>`: ¿existe? ¿longitud 150-160 chars? ¿persuasiva?
- `<meta viewport>`: ¿existe?
- `<meta robots>`: ¿bloquea indexación sin querer?
- `<link canonical>`: ¿existe y apunta bien?
- Idioma: `<html lang="xx">` definido

**2. Headings (15%)**
- ¿Hay exactamente un `<h1>`?
- ¿La jerarquía es correcta? (no saltar de h1 a h3)
- ¿El h1 contiene la keyword principal (si se proporcionó)?
- ¿Los h2 son descriptivos del contenido?

**3. Imágenes (10%)**
- Total de imágenes
- ¿Cuántas tienen atributo `alt` descriptivo?
- ¿Hay `loading="lazy"` en imágenes below the fold?
- ¿Se usan formatos modernos (WebP, AVIF)?

**4. Enlaces (10%)**
- Total internos vs externos
- ¿Hay enlaces rotos (404)?
- ¿Los externos tienen `rel="noopener"` o `rel="nofollow"` cuando corresponde?
- ¿Los textos ancla son descriptivos? (no "click aquí", "ver más")

**5. Open Graph y Social (10%)**
- og:title, og:description, og:image, og:url, og:type — ¿completos?
- twitter:card, twitter:title, twitter:description, twitter:image
- ¿Las longitudes son correctas? ¿La imagen OG existe?

**6. Schema / Datos Estructurados (10%)**
- ¿Hay JSON-LD, Microdata o RDFa?
- ¿Qué tipos? (Organization, LocalBusiness, Article, Product, etc.)
- ¿Está bien formado el JSON?
- ¿Faltan campos importantes?

**7. Técnico (15%)**
- Tiempo de respuesta del servidor
- ¿HTTPS activo?
- ¿Robots.txt presente y correcto?
- ¿Sitemap.xml presente y accesible?
- ¿Favicon presente?
- Tamaño del HTML
- Redirecciones www vs no-www configuradas

**8. Contenido (10%)**
- Conteo de palabras del texto visible
- Ratio texto/HTML (debería ser >25%)
- ¿Hay contenido suficiente? (>300 palabras para páginas principales)
- ¿Title y description son únicos?

### Puntuación global

Media ponderada de las 8 categorías según los pesos indicados.

---

## Paso 4 — Generar el dashboard HTML

Genera un único archivo HTML autocontenido con todo el informe. Libertad creativa total en el diseño, pero debe incluir:

### Contenido obligatorio del dashboard

1. **Header** — URL auditada, fecha de la auditoría, puntuación global en un elemento visual grande y claro. Color según resultado: verde (80+), amarillo (50-79), rojo (<50).

2. **Resumen ejecutivo** — 4 tarjetas:
   - Puntuación global
   - Problemas críticos (count)
   - Advertencias (count)
   - Tests aprobados (count)

3. **Top 5 correcciones prioritarias** — Lo más importante. Ordenadas por impacto real en SEO. Cada una con:
   - Qué está mal (concreto)
   - Por qué importa (impacto en Google)
   - Cómo corregirlo (código exacto o instrucción clara que cualquier persona pueda seguir)

4. **Desglose por categoría** — Las 8 categorías con:
   - Barra de progreso visual con puntuación
   - Lista de hallazgos con estado (aprobado / advertencia / error)
   - Recomendación para cada problema

5. **Comparativa con competidores** — Solo si el usuario proporcionó URLs de competidores. Tabla lado a lado con puntuaciones por categoría.

6. **Detalle técnico completo** — Tabla expandible/colapsable con TODOS los hallazgos para quien quiera profundizar.

### Requisitos del dashboard

- Responsive (se ve bien en móvil)
- Autocontenido (CSS y JS inline, sin dependencias)
- Imprimible (que al imprimir/exportar PDF se vea bien)
- Con navegación interna (links a cada sección)

---

## Paso 5 — Guardar y presentar

- Guarda como `auditoria-seo-[dominio].html` (dominio en kebab-case)
- Abre automáticamente en el navegador

Presenta un resumen breve:

1. **Puntuación global** y nivel (bueno/mejorable/crítico)
2. **Top 3 correcciones** más urgentes en una frase cada una
3. **Qué secciones tiene el informe** para que sepa qué encontrar
4. Pregunta si quiere que **aplique las correcciones directamente** en su código (si tiene el código fuente accesible)

No muestres precios sugeridos ni consejos de venta.

---

## Paso 6 — Aplicar correcciones (opcional)

Si el usuario dice que sí y tiene los archivos del sitio accesibles:

1. Localiza los archivos HTML/template relevantes
2. Aplica las correcciones una por una (meta tags, alts, headings, schema, etc.)
3. Muestra cada cambio realizado
4. Ofrece volver a ejecutar la auditoría para ver la mejora en puntuación
