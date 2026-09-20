import os

# Render dynamically assigns a port via the PORT environment variable (default: 10000)
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Worker configuration optimized for Render free/starter tier
workers = 2
threads = 4
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
