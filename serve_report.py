#!/usr/bin/env python3
"""
Serve a lead report HTML with CRM API proxy.

Usage:
    python serve_report.py [--port PORT] [--open] [report.html]

Environment variables (from .env.local or .env):
    CRM_API_URL     — Base URL of the CRM (default: https://crm.juancode.dev)
    CRM_API_EMAIL   — Login email for CRM auth
    CRM_API_PASSWORD — Login password for CRM auth

The server:
  1. Reads CRM credentials from env vars
  2. Authenticates with the CRM to get a JWT token
  3. Serves the HTML report at http://localhost:<port>
  4. POST /api/send-lead proxies lead creation to the CRM
"""

import argparse
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ── Cargar .env.local ──
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__) or ".", ".env.local"))
    load_dotenv(os.path.join(os.path.dirname(__file__) or ".", ".env"))
except ImportError:
    pass

# ── Config ──
CRM_API_URL = os.environ.get("CRM_API_URL", "https://crm.juancode.dev")
CRM_EMAIL = os.environ.get("CRM_API_EMAIL", "")
CRM_PASSWORD = os.environ.get("CRM_API_PASSWORD", "")

CRM_COOKIE: str | None = None  # Supabase session cookie (set after auth)


# ── CRM Auth ──
def authenticate() -> str | None:
    """
    Authenticate with the CRM and return the Supabase session cookie.
    
    The CRM is a Next.js app with Supabase SSR — API routes read the session
    from the sb-*-auth-token cookie, NOT from the Authorization header.
    """
    if not CRM_EMAIL or not CRM_PASSWORD:
        print("✗ CRM_API_EMAIL y CRM_API_PASSWORD no están configuradas en .env.local")
        return None

    url = f"{CRM_API_URL}/api/auth/login"
    payload = json.dumps({"email": CRM_EMAIL, "password": CRM_PASSWORD}).encode()

    try:
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=15) as resp:
            resp.read().decode()  # drain body

            # Extract the Supabase session cookie
            set_cookie = resp.getheader("set-cookie", "")
            for part in set_cookie.split(","):
                if "sb-" in part:
                    cookie = part.split(";")[0]
                    print(f"✓ Autenticado en CRM como {CRM_EMAIL}")
                    return cookie

            print("✗ No se encontró cookie de sesión Supabase en la respuesta")
            return None
    except HTTPError as e:
        body = e.read().decode()
        try:
            detail = json.loads(body)
            err_msg = detail.get("error", detail.get("detail", body))
        except json.JSONDecodeError:
            err_msg = body
        print(f"✗ Error de autenticación CRM ({e.code}): {err_msg}")
        return None
    except URLError as e:
        print(f"✗ No se pudo conectar al CRM ({e.reason})")
        return None


# ── HTTP Handler ──
class ReportHandler(SimpleHTTPRequestHandler):
    """Serves static files + proxies lead creation to CRM."""

    def do_POST(self):
        if self.path == "/api/send-lead":
            self._handle_send_lead()
        else:
            self.send_error(404, "Ruta no encontrada")

    def _handle_send_lead(self):
        global CRM_COOKIE

        if not CRM_COOKIE:
            self._json_response(401, {"error": "No autenticado. Revisa CRM_API_EMAIL y CRM_API_PASSWORD"})
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            self._json_response(400, {"error": "Body vacío"})
            return

        try:
            body = json.loads(self.rfile.read(length).decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_response(400, {"error": "JSON inválido"})
            return

        # Forward to CRM using Supabase session cookie (not Bearer token)
        crm_url = f"{CRM_API_URL}/api/leads"
        payload = json.dumps(body).encode()
        req = Request(
            crm_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Cookie": CRM_COOKIE,
            },
        )

        try:
            with urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
                self._json_response(201, result)
        except HTTPError as e:
            error_body = e.read().decode()
            try:
                detail = json.loads(error_body)
            except json.JSONDecodeError:
                detail = {"error": error_body}
            self._json_response(e.code, detail)
        except URLError as e:
            self._json_response(502, {"error": f"Error de conexión con CRM: {e.reason}"})

    def _json_response(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    # Suppress default logging to stderr
    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Sirve el reporte HTML de leads con proxy al CRM")
    parser.add_argument("--port", type=int, default=8765, help="Puerto (default: 8765)")
    parser.add_argument("--no-open", action="store_true", help="No abrir el navegador automáticamente")
    parser.add_argument("report", nargs="?", default="", help="Ruta al archivo HTML del reporte")
    args = parser.parse_args()

    # Report path
    report_path = args.report
    if not report_path:
        # Try to find the latest .html in leads_output
        leads_dir = os.path.join(os.path.dirname(__file__) or ".", "leads_output")
        if os.path.isdir(leads_dir):
            htmls = [f for f in os.listdir(leads_dir) if f.endswith(".html") and "audit" not in f]
            if htmls:
                # Pick the most recent by modification time
                htmls.sort(key=lambda f: os.path.getmtime(os.path.join(leads_dir, f)), reverse=True)
                report_path = os.path.join(leads_dir, htmls[0])
                print(f"ℹ Usando reporte más reciente: {report_path}")
            else:
                print("✗ No se encontraron archivos .html en leads_output/")
                sys.exit(1)
        else:
            print("✗ No se especificó reporte y no existe leads_output/")
            sys.exit(1)

    if not os.path.isfile(report_path):
        print(f"✗ Archivo no encontrado: {report_path}")
        sys.exit(1)

    # Auth with CRM
    global CRM_COOKIE
    CRM_COOKIE = authenticate()
    if not CRM_COOKIE:
        print("⚠ El reporte se servirá sin integración CRM")
        print("  Los botones 'Enviar al CRM' mostrarán error hasta que configures las credenciales.")

    report_dir = os.path.dirname(os.path.abspath(report_path)) or "."
    os.chdir(report_dir)
    server = HTTPServer(("0.0.0.0", args.port), ReportHandler)

    print(f"\n{'='*50}")
    print(f"  Reporte de Leads")
    print(f"  Servidor: http://localhost:{args.port}")
    print(f"  Archivo: {os.path.basename(report_path)}")
    print(f"  CRM: {'✓ Conectado' if CRM_COOKIE else '✗ No configurado'}")
    print(f"{'='*50}\n")
    print("Presiona Ctrl+C para detener el servidor\n")

    # Open browser
    if not args.no_open:
        import webbrowser
        webbrowser.open(f"http://localhost:{args.port}/{os.path.basename(report_path)}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
