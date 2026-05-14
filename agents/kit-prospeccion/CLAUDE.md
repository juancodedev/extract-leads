# Prospección de Clientes

Este proyecto busca clientes potenciales en cualquier sector y ciudad, analiza su presencia digital y genera un informe con las mejores oportunidades y datos de contacto.

## Comportamiento al iniciar

Cuando el usuario abra esta carpeta y escriba cualquier cosa, responde:

> **Bienvenido al buscador de clientes potenciales**
>
> Voy a buscar negocios de tu sector, analizar su presencia digital y encontrar los que más necesitan tus servicios.
>
> Necesito 3 cosas:
> 1. **¿Qué tipo de negocio buscas?** (restaurantes, clínicas, gimnasios, abogados...)
> 2. **¿En qué ciudad o zona?**
> 3. **¿Qué servicio les vas a ofrecer?** (diseño web, SEO, marketing, automatización...)

Después usa la skill `prospeccion` automáticamente.

## Qué hace

1. Busca negocios reales del sector y ciudad indicados
2. Analiza la web de cada uno (HTTPS, responsive, SEO, redes sociales...)
3. Puntúa la oportunidad de cada negocio según el servicio que ofreces
4. Genera un informe HTML con tabla de prospectos, análisis detallado de los mejores, y mensajes de contacto personalizados
5. Exporta los datos en JSON para importar en CRM o Google Sheets

## No necesita nada instalado

Claude usa WebSearch y WebFetch nativos. Si tienes Firecrawl o Playwright, los usará para resultados más completos.
