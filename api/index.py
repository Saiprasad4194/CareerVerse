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
    1. Reads __path__ or path from query string if passed by vercel.json rewrite (e.g. ?__path__=/navigator).
    2. Falls back to HTTP_X_FORWARDED_URI, HTTP_X_MATCHED_PATH, or RAW_URI.
    3. Restores WSGI PATH_INFO so Flask routes match accurately.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        target_path = None

        if query_string:
            try:
                parsed_qs = urllib.parse.parse_qs(query_string, keep_blank_values=True)
                for key in ("__path__", "path"):
                    if key in parsed_qs:
                        raw_val = parsed_qs[key][0].strip()
                        cleaned_val = raw_val.lstrip("/")
                        if cleaned_val:
                            target_path = "/" + cleaned_val
                        # Clean the routing parameter from QUERY_STRING
                        cleaned_pairs = []
                        for k, vlist in parsed_qs.items():
                            if k not in ("__path__", "path"):
                                for v in vlist:
                                    cleaned_pairs.append(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(v)}")
                        environ["QUERY_STRING"] = "&".join(cleaned_pairs)
                        break
            except Exception as e:
                print(f"[PATH_MIDDLEWARE QS ERROR] {e}", file=sys.stderr)

        # Fallback to proxy/Vercel headers if target_path not found
        if not target_path or target_path == "/":
            raw_target = (
                environ.get("HTTP_X_FORWARDED_URI") or
                environ.get("HTTP_X_MATCHED_PATH") or
                environ.get("HTTP_X_ORIGINAL_URI") or
                environ.get("RAW_URI")
            )
            if raw_target:
                clean = raw_target.split("?")[0].strip().lstrip("/")
                if clean and not clean.startswith("api/index") and clean != "app.py":
                    target_path = "/" + clean

        if target_path:
            if target_path in ("/api/index.py", "/api/index", "/api", "/app.py"):
                environ["PATH_INFO"] = "/"
            else:
                environ["PATH_INFO"] = target_path
        elif environ.get("PATH_INFO", "") in ("/api/index.py", "/api/index", "/api", "/app.py"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
handler = app
