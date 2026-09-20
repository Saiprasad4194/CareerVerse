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
    On Vercel:
    1. Reads __path__ from query string if passed by vercel.json rewrite (e.g. ?__path__=/navigator).
    2. Falls back to HTTP_X_FORWARDED_URI, HTTP_X_MATCHED_PATH, or RAW_URI.
    3. Restores WSGI PATH_INFO so Flask routes match accurately.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        target_path = None

        if "__path__=" in query_string:
            try:
                parsed_qs = urllib.parse.parse_qs(query_string, keep_blank_values=True)
                if "__path__" in parsed_qs:
                    val = parsed_qs["__path__"][0].strip()
                    target_path = "/" + val.lstrip("/") if val else "/"
                    # Remove __path__ from QUERY_STRING so application doesn't see it
                    cleaned_pairs = []
                    for k, vlist in parsed_qs.items():
                        if k != "__path__":
                            for v in vlist:
                                cleaned_pairs.append(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(v)}")
                    environ["QUERY_STRING"] = "&".join(cleaned_pairs)
            except Exception:
                pass

        if not target_path:
            raw_target = (
                environ.get("HTTP_X_FORWARDED_URI") or
                environ.get("HTTP_X_MATCHED_PATH") or
                environ.get("HTTP_X_ORIGINAL_URI") or
                environ.get("RAW_URI")
            )
            if raw_target:
                clean = raw_target.split("?")[0].strip()
                if clean and not clean.startswith("/api/index"):
                    target_path = clean

        if target_path:
            environ["PATH_INFO"] = target_path
        elif environ.get("PATH_INFO", "") in ("/api/index.py", "/api/index", "/api", "/app.py"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
handler = app
