import os
import sys
import urllib.parse

# Ensure the root project directory is first in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app


class VercelPathMiddleware:
    """
    WSGI Middleware to accurately restore PATH_INFO for Vercel Serverless deployments.
    Handles Vercel proxy headers (x-now-route-matches, x-matched-path, x-forwarded-uri),
    query string routing parameters, and direct path resolution.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        target_path = None

        # 1. Check HTTP_X_NOW_ROUTE_MATCHES (Vercel sets this when using named/regex capture groups)
        matches = environ.get("HTTP_X_NOW_ROUTE_MATCHES")
        if matches:
            try:
                parsed = urllib.parse.parse_qs(matches)
                for key in ("path", "1", "0"):
                    if key in parsed and parsed[key][0]:
                        raw = parsed[key][0].strip().lstrip("/")
                        if raw and not raw.startswith("api/index") and raw != "app.py" and not raw.startswith("$"):
                            target_path = "/" + raw
                            break
                        elif not raw:
                            target_path = "/"
                            break
            except Exception as e:
                print(f"[PATH_MIDDLEWARE MATCHES ERROR] {e}", file=sys.stderr)

        # 2. Check standard proxy & Vercel headers
        if not target_path or target_path == "/":
            for header_key in (
                "HTTP_X_MATCHED_PATH",
                "HTTP_X_FORWARDED_URI",
                "HTTP_X_ORIGINAL_URI",
                "HTTP_X_VERCEL_MATCHED_PATH",
                "REQUEST_URI",
                "RAW_URI"
            ):
                raw_val = environ.get(header_key)
                if raw_val:
                    cleaned = raw_val.split("?")[0].strip().lstrip("/")
                    if cleaned and not cleaned.startswith("api/index") and cleaned != "app.py" and not cleaned.startswith("$"):
                        target_path = "/" + cleaned
                        break

        # 3. Fallback to existing PATH_INFO
        if not target_path:
            current_path = environ.get("PATH_INFO", "")
            if current_path and current_path not in ("/api/index.py", "/api/index", "/api", "/app.py"):
                target_path = current_path
            else:
                target_path = "/"

        environ["PATH_INFO"] = target_path
        return self.wsgi_app(environ, start_response)


app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
handler = app
