import os
import sys

# Ensure the root project directory is first in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

class VercelPathMiddleware:
    """
    On Vercel, URL rewrites to /api/index.py set WSGI PATH_INFO to '/api/index.py'.
    The real client URL path is provided in HTTP_X_MATCHED_PATH or HTTP_X_FORWARDED_URI.
    This middleware restores the original PATH_INFO so Flask routes match seamlessly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get("HTTP_X_MATCHED_PATH") or
            environ.get("HTTP_X_FORWARDED_URI") or
            environ.get("HTTP_X_ORIGINAL_URI") or
            environ.get("RAW_URI")
        )
        if matched_path:
            clean_path = matched_path.split("?")[0].strip()
            if clean_path and clean_path != "/api/index.py":
                environ["PATH_INFO"] = clean_path
            elif clean_path == "/api/index.py":
                environ["PATH_INFO"] = "/"
        elif environ.get("PATH_INFO") in ("/api/index.py", "/api/index", "/api", "/app.py"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
handler = app
