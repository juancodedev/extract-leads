"""
Website analyzer for leads - checks availability, SEO, booking systems,
images, performance, and generates actionable improvement suggestions.
"""

import asyncio
import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import aiohttp
from tqdm import tqdm

from booking_data import BOOKING_DOMAINS, BOOKING_SKIP

logger = logging.getLogger(__name__)

CMS_PATTERNS = {
    "WordPress": [r"wp-content", r"wp-json", r"wp-includes", r"wordpress"],
    "Shopify": [r"myshopify\.com", r"shopify\.com", r"cdn\.shopify"],
    "Wix": [r"wix\.com", r"wixstatic\.com", r"Wix\.js"],
    "Squarespace": [r"squarespace\.com", r"static1\.squarespace"],
    "Joomla": [r"joomla", r"com_content"],
    "Drupal": [r"drupal", r"core\/misc\/drupal"],
    "PrestaShop": [r"prestashop", r"ps_shoppingcart"],
    "Magento": [r"magento", r"mage\/"],
    "Webflow": [r"webflow", r"assets\.website-files"],
    "Bubble": [r"bubble\.io", r"bubbleapps"],
    "UENI": [r"ueniweb\.com", r"ueni\.com"],
    "AgendaPro": [r"agendapro\.com"],
    "MiNegocio": [r"sitemi\.cl"],
}

TITLE_TRUNCATE = 100
DESC_TRUNCATE = 150
H1_TRUNCATE = 80
SLOW_THRESHOLD_MS = 3000
WARN_THRESHOLD_MS = 1500
TITLE_MIN = 30
TITLE_IDEAL_MIN = 50
TITLE_IDEAL_MAX = 70
CONTENT_SPARSE = 100
CONTENT_LOW = 300
MAX_IMPROVEMENTS = 12
TECH_BASE_SCORE = 50
TECH_MAX_SCORE = 100
TECH_GREEN_THRESHOLD = 80
TECH_YELLOW_THRESHOLD = 50


class WebsiteAnalyzer:
    """Analyze a business website for quality signals and improvements."""

    def __init__(
        self, session: aiohttp.ClientSession, timeout: int = 15, config: dict | None = None
    ):
        self.session = session
        self.timeout = timeout
        self._sem = asyncio.Semaphore(10)
        sc_cfg = (config or {}).get("scoring", {}).get("thresholds", {})
        self.slow_threshold = sc_cfg.get("slow_ms", SLOW_THRESHOLD_MS)
        self.warn_threshold = sc_cfg.get("warn_ms", WARN_THRESHOLD_MS)

    async def analyze(self, url: str) -> dict[str, Any]:
        """Run full analysis on a website URL."""
        result: dict[str, Any] = {
            "url": url,
            "url_clean": self._clean_url(url),
            "status": "error",
            "status_code": 0,
            "response_time_ms": 0,
            "error": None,
            "ssl": False,
            "redirects": 0,
            "final_url": "",
        }

        if not url:
            result["error"] = "No URL provided"
            return result

        clean_url = result["url_clean"]
        if not clean_url:
            result["error"] = "Invalid URL"
            return result

        start = time.time()
        try:
            async with (
                self._sem,
                self.session.get(
                    clean_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=True,
                ) as resp,
            ):
                try:
                    html = await resp.text()
                except (UnicodeDecodeError, UnicodeError):
                    raw = await resp.read()
                    charset = resp.charset or "utf-8"
                    html = raw.decode(charset, errors="replace")
                    result["warnings"] = result.get("warnings", [])
                    result["warnings"].append("encoding_fallback")

                elapsed = int((time.time() - start) * 1000)

                result["status"] = "ok" if resp.status == 200 else "warning"
                result["status_code"] = resp.status
                result["response_time_ms"] = elapsed
                result["ssl"] = clean_url.startswith("https")
                result["redirects"] = len(resp.history)
                result["final_url"] = str(resp.url)

                result.update(self._analyze_html(html))
                result.update(self._analyze_headers(resp.headers))  # type: ignore[arg-type]
                result["improvements"] = self._generate_improvements(result)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            elapsed = int((time.time() - start) * 1000)
            if isinstance(e, asyncio.TimeoutError):
                result["error"] = f"Timeout after {self.timeout}s"
                result["response_time_ms"] = elapsed
            else:
                result["error"] = str(e)[:100]

        return result

    def _clean_url(self, url: str) -> str:
        if not url:
            return ""
        url = url.strip()
        if not url.startswith("http"):
            url = "https://" + url
        parsed = urlparse(url)
        if not parsed.netloc:
            return ""
        return url

    def _analyze_html(self, html: str) -> dict:
        analysis = {
            "page_size_kb": len(html) // 1024,
            "seo": self._analyze_seo(html),
            "images": self._analyze_images(html),
            "booking": self._analyze_booking(html),
            "contact": self._analyze_contact(html),
            "content": self._analyze_content(html),
            "mobile": self._analyze_mobile(html),
            "tech_stack": self._detect_cms(html),
        }
        return analysis

    def _analyze_seo(self, html: str) -> dict:
        seo = {
            "has_title": False,
            "title": "",
            "title_length": 0,
            "has_meta_description": False,
            "meta_description": "",
            "meta_description_length": 0,
            "has_og_title": False,
            "has_og_description": False,
            "has_og_image": False,
            "has_canonical": False,
            "has_h1": False,
            "h1_count": 0,
            "h1_text": "",
            "has_robots": False,
            "has_sitemap": False,
            "has_favicon": False,
            "has_schema_org": False,
        }

        # Title
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
        if m:
            title = m.group(1).strip()
            seo["has_title"] = bool(title)
            seo["title"] = title[:TITLE_TRUNCATE]
            seo["title_length"] = len(title)

        # Meta description
        m = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
            html,
            re.IGNORECASE,
        )
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
                html,
                re.IGNORECASE,
            )
        if m:
            desc = m.group(1).strip()
            seo["has_meta_description"] = bool(desc)
            seo["meta_description"] = desc[:DESC_TRUNCATE]
            seo["meta_description_length"] = len(desc)

        # OG tags
        if re.search(r'property=["\']og:title["\']', html, re.IGNORECASE):
            seo["has_og_title"] = True
        if re.search(r'property=["\']og:description["\']', html, re.IGNORECASE):
            seo["has_og_description"] = True
        if re.search(r'property=["\']og:image["\']', html, re.IGNORECASE):
            seo["has_og_image"] = True

        # Canonical
        if re.search(r'rel=["\']canonical["\']', html, re.IGNORECASE):
            seo["has_canonical"] = True

        # H1
        h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
        seo["has_h1"] = len(h1s) > 0
        seo["h1_count"] = len(h1s)
        if h1s:
            seo["h1_text"] = re.sub(r"<[^>]+>", "", h1s[0]).strip()[:H1_TRUNCATE]

        # Robots meta
        if re.search(r'name=["\']robots["\']', html, re.IGNORECASE):
            seo["has_robots"] = True

        # Sitemap
        if re.search(r"sitemap", html, re.IGNORECASE):
            seo["has_sitemap"] = True

        # Favicon
        if re.search(r'rel=["\'](?:shortcut )?icon["\']', html, re.IGNORECASE):
            seo["has_favicon"] = True

        # Schema.org
        if re.search(r"schema\.org", html, re.IGNORECASE) or re.search(
            r"application/ld\+json", html, re.IGNORECASE
        ):
            seo["has_schema_org"] = True

        return seo

    def _analyze_images(self, html: str) -> dict:
        images = re.findall(r"<img[^>]+>", html, re.IGNORECASE)
        total = len(images)
        without_alt = 0
        has_lazy = False

        for img in images:
            if not re.search(r'alt=["\']', img, re.IGNORECASE):
                without_alt += 1
            if re.search(r'loading=["\']lazy["\']', img, re.IGNORECASE):
                has_lazy = True

        return {
            "total": total,
            "without_alt": without_alt,
            "has_lazy_loading": has_lazy,
        }

    def _analyze_booking(self, html: str) -> dict:
        result: dict[str, Any] = {
            "has_booking": False,
            "systems": [],
            "links": [],
        }

        for domain, name in BOOKING_DOMAINS.items():
            pattern = re.escape(domain)
            for m in re.finditer(
                r'https?://[^"\'<>\s]*' + pattern + r'[^"\'<>\s]*',
                html,
            ):
                link = m.group(0)
                link_lower = link.lower()
                if any(skip in link_lower for skip in BOOKING_SKIP):
                    continue
                result["has_booking"] = True
                if name not in result["systems"]:
                    result["systems"].append(name)
                result["links"].append(link)

        return result

    def _analyze_contact(self, html: str) -> dict:
        return {
            "has_whatsapp": bool(
                re.search(
                    r"(wa\.me|api\.whatsapp|whatsapp\.com/send)",
                    html,
                    re.IGNORECASE,
                )
            ),
            "has_contact_form": bool(
                re.search(
                    r"(<form[^>]*>.*?</form>)",
                    html,
                    re.DOTALL | re.IGNORECASE,
                )
            ),
            "has_email_link": bool(
                re.search(
                    r"mailto:[a-zA-Z0-9@._-]+",
                    html,
                )
            ),
            "has_phone_link": bool(
                re.search(
                    r"tel:\+?\d+",
                    html,
                )
            ),
            "has_social_links": bool(
                re.search(
                    r"(facebook\.com|instagram\.com|linkedin\.com)",
                    html,
                    re.IGNORECASE,
                )
            ),
            "has_google_maps_embed": bool(
                re.search(
                    r"google\.com/maps|maps\.google",
                    html,
                    re.IGNORECASE,
                )
            ),
        }

    def _analyze_content(self, html: str) -> dict:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        word_count = len(text.split())

        return {
            "word_count": word_count,
            "has_cta": bool(
                re.search(
                    r"(reservar|agendar|comprar|contactar|llamar|comenzar|empezar|solicitar|cotizar|más info|ver más|lo quiero)",
                    html,
                    re.IGNORECASE,
                )
            ),
            "has_testimonials": bool(
                re.search(
                    r"(testimonio|reseña|opinión|cliente dice|recomiendo|★★★★★|estrellas)",
                    html,
                    re.IGNORECASE,
                )
            ),
            "has_blog": bool(
                re.search(
                    r"(/blog|/noticias|articulo|posts?\b)",
                    html,
                    re.IGNORECASE,
                )
            ),
            "has_prices": bool(
                re.search(
                    r"(CLP|UF|precio|valor|desde \$\$|tarifa|cuota)",
                    html,
                    re.IGNORECASE,
                )
            ),
            "has_gallery": bool(
                re.search(
                    r"(galería|galeria|portfolio|trabajos|proyectos)",
                    html,
                    re.IGNORECASE,
                )
            ),
        }

    def _analyze_mobile(self, html: str) -> dict:
        return {
            "has_viewport": bool(
                re.search(
                    r'name=["\']viewport["\']',
                    html,
                    re.IGNORECASE,
                )
            ),
            "has_responsive_css": bool(
                re.search(r"@media\s*\(", html),
            ),
        }

    def _analyze_headers(self, headers: dict) -> dict:
        perf = {
            "has_gzip": False,
            "server": "",
        }
        encoding = headers.get("Content-Encoding", "")
        perf["has_gzip"] = "gzip" in encoding
        perf["server"] = headers.get("Server", "")
        return {"performance": perf}

    def _detect_cms(self, html: str) -> list[str]:
        detected = []
        for cms_name, patterns in CMS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    detected.append(cms_name)
                    break
        return detected if detected else ["Custom / Unknown"]

    def _generate_improvements(self, analysis: dict) -> list[str]:
        improvements = []
        seo = analysis.get("seo", {})
        images = analysis.get("images", {})
        contact = analysis.get("contact", {})
        content = analysis.get("content", {})
        mobile = analysis.get("mobile", {})
        perf = analysis.get("performance", {})

        # Status
        code = analysis.get("status_code", 0)
        if code == 0:
            improvements.append("❌ Sitio web no accesible")
        elif code == 404:
            improvements.append("❌ Página no encontrada (404)")
        elif code >= 500:
            improvements.append(f"❌ Error del servidor ({code})")
        elif code >= 300:
            improvements.append(f"⚠️ Redirección detectada ({code})")
        elif code == 200:
            improvements.append("✅ Sitio web accesible y funcionando")

        # SSL
        if not analysis.get("ssl"):
            improvements.append("🔒 SSL no detectado — migrar a HTTPS")

        # Performance
        rt = analysis.get("response_time_ms", 0)
        if rt > self.slow_threshold:
            improvements.append(f"🐌 Carga lenta: {rt}ms (ideal < 2s)")
        elif rt > self.warn_threshold:
            improvements.append(f"⏱️ Tiempo de carga mejorable: {rt}ms")
        else:
            improvements.append(f"⚡ Carga rápida: {rt}ms")

        if not perf.get("has_gzip"):
            improvements.append("🗜️ Habilitar compresión Gzip")

        # SEO
        if not seo.get("has_title"):
            improvements.append("📄 Falta etiqueta <title>")
        else:
            tl = seo.get("title_length", 0)
            if tl < TITLE_MIN:
                improvements.append(f"📄 Title muy corto ({tl} chars) — ideal 50-60")
            elif tl > TITLE_IDEAL_MAX:
                improvements.append(f"📄 Title muy largo ({tl} chars) — ideal 50-60")
            else:
                improvements.append(f"📄 Title OK ({tl} chars)")

        if not seo.get("has_meta_description"):
            improvements.append("📝 Falta meta description")
        else:
            ml = seo.get("meta_description_length", 0)
            if ml < 80:
                improvements.append(f"📝 Meta description corta ({ml} chars) — ideal 120-160")
            elif ml > 170:
                improvements.append(f"📝 Meta description larga ({ml} chars) — ideal 120-160")
            else:
                improvements.append(f"📝 Meta description OK ({ml} chars)")

        if not seo.get("has_og_title"):
            improvements.append("🔗 Falta Open Graph title (compartir en redes)")
        if not seo.get("has_og_image"):
            improvements.append("🖼️ Falta Open Graph image (vista previa en redes)")
        if not seo.get("has_canonical"):
            improvements.append("🔗 Falta etiqueta canonical (evitar contenido duplicado)")
        if not seo.get("has_h1"):
            improvements.append("📑 Falta etiqueta H1 en la página")
        elif seo.get("h1_count", 0) > 1:
            improvements.append(f"📑 {seo['h1_count']} H1 detectados — debe haber solo 1")
        else:
            improvements.append(f"📑 H1: \"{seo.get('h1_text', '')[:40]}...\"")
        if not seo.get("has_favicon"):
            improvements.append("🏷️ Falta favicon")
        if not seo.get("has_schema_org"):
            improvements.append("📊 Falta Schema.org / datos estructurados")

        # Images
        img_total = images.get("total", 0)
        img_no_alt = images.get("without_alt", 0)
        if img_total == 0:
            improvements.append("🖼️ No se detectaron imágenes en la página")
        else:
            improvements.append(f"🖼️ {img_total} imágenes en página")
            if img_no_alt > 0:
                improvements.append(
                    f"🖼️ {img_no_alt} imágenes sin atributo alt (accesibilidad + SEO)"
                )
        if not images.get("has_lazy_loading"):
            improvements.append("📸 Falta lazy loading en imágenes (mejora velocidad)")

        # Mobile
        if not mobile.get("has_viewport"):
            improvements.append("📱 Falta viewport meta — el sitio no es mobile-friendly")
        if not mobile.get("has_responsive_css"):
            improvements.append("📱 No se detectaron media queries — posiblemente no responsive")

        # Contact
        if not contact.get("has_whatsapp"):
            improvements.append("💬 Agregar botón de WhatsApp (alta conversión en Chile)")
        if not contact.get("has_phone_link"):
            improvements.append("📞 Agregar enlace clickable al teléfono (tel:)")
        if not contact.get("has_contact_form"):
            improvements.append("📝 Agregar formulario de contacto")
        if not contact.get("has_social_links"):
            improvements.append("🔗 Agregar enlaces a redes sociales")
        if not contact.get("has_google_maps_embed"):
            improvements.append("📍 Agregar mapa de Google Maps embebido")

        # Booking
        booking = analysis.get("booking", {})
        if booking.get("has_booking"):
            systems = ", ".join(booking.get("systems", []))
            improvements.append(f"📅 Sistema de reservas detectado: {systems}")
        else:
            improvements.append("📅 No tiene sistema de reservas online — oportunidad")

        # Content
        wc = content.get("word_count", 0)
        if wc < CONTENT_SPARSE:
            improvements.append(f"📝 Contenido escaso: {wc} palabras (ideal > 300)")
        elif wc < CONTENT_LOW:
            improvements.append(f"📝 Poco contenido: {wc} palabras")
        else:
            improvements.append(f"📝 Buen contenido: {wc} palabras")

        if not content.get("has_cta"):
            improvements.append("🎯 No hay llamado a la acción claro (CTA)")
        if not content.get("has_testimonials"):
            improvements.append("⭐ No hay testimonios o reseñas visibles")
        if not content.get("has_blog"):
            improvements.append("📰 No tiene blog — contenido freso ayuda al SEO")
        if not content.get("has_prices"):
            improvements.append("💰 No muestra precios o tarifas")
        if content.get("has_gallery"):
            improvements.append("🖼️ Tiene galería de trabajos 👍")

        # CMS
        tech = analysis.get("tech_stack", [])
        if "UENI" in tech:
            improvements.append(
                "🏗️ Creado con UENI — considerar migrar a plataforma más profesional"
            )
        if "WordPress" not in tech and "Custom" not in tech:
            pass  # No strong opinion

        return improvements


async def generate_audit_report(leads: list[dict], output_path: str):
    """Run website analysis on all leads with websites and generate HTML report."""
    from reporters import export_audit_html

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        analyzer = WebsiteAnalyzer(session)
        total = len(leads)
        with_website = [lead for lead in leads if lead.get("website")]
        with_website = sorted(with_website, key=lambda x: x.get("lead_score", 0), reverse=True)

        logger.info("Auditing %d/%d websites...", len(with_website), total)

        results = []
        pbar = tqdm(with_website, desc="Auditing websites", unit="site")
        for lead in pbar:
            url = lead["website"]
            name = lead.get("business_name", "")
            pbar.set_postfix_str(name[:30])
            analysis = await analyzer.analyze(url)
            analysis["business_name"] = name
            analysis["industry"] = lead.get("industry", "")
            analysis["city"] = lead.get("city", "")
            analysis["phone"] = lead.get("phone", "")
            analysis["lead_score"] = lead.get("lead_score", 0)
            analysis["lead_tier"] = lead.get("lead_tier", "COLD")
            results.append(analysis)

        pbar.close()

        export_audit_html(results, output_path, total, len(with_website))
