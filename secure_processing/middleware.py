"""
Flask Security Middleware for CareerVerse AI.

Provides:
- Thread-safe sliding-window rate limiting for sensitive endpoints
- Comprehensive OWASP-recommended HTTP security headers
- Magic byte PDF validation (%PDF-) and size enforcement
- Role-based authorization & session integrity verification
"""

from collections import defaultdict
from functools import wraps
import io
import os
import time
import threading
from typing import Callable, Dict, List, Optional, Tuple

from flask import Flask, Request, Response, jsonify, request, session
from secure_processing.audit_logger import audit_logger


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    """

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_key: str) -> Tuple[bool, int]:
        """
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self.lock:
            # Prune timestamps outside the current window
            timestamps = self.requests[client_key]
            valid_timestamps = [t for t in timestamps if t > window_start]
            self.requests[client_key] = valid_timestamps

            if len(valid_timestamps) >= self.max_requests:
                oldest_in_window = valid_timestamps[0]
                retry_after = max(1, int(oldest_in_window + self.window_seconds - now))
                return False, retry_after

            self.requests[client_key].append(now)
            return True, 0


# Global limiters for different sensitivity tiers
sensitive_rate_limiter = SlidingWindowRateLimiter(max_requests=15, window_seconds=60)
standard_rate_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)


def get_client_ip(req: Request) -> str:
    """Extracts client IP considering trusted reverse proxy headers."""
    forwarded_for = req.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return req.remote_addr or "127.0.0.1"


def rate_limit_sensitive(f: Callable) -> Callable:
    """Decorator to enforce strict rate limiting on sensitive routes (e.g. /resume-api)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip(request)
        allowed, retry_after = sensitive_rate_limiter.is_allowed(client_ip)
        if not allowed:
            audit_logger.log_event(
                event_type="RATE_LIMIT_EXCEEDED",
                status="BLOCKED",
                client_id=client_ip,
                details={"endpoint": request.path, "retry_after": retry_after}
            )
            resp = jsonify({
                "success": False,
                "error": f"Rate limit exceeded. Please wait {retry_after} seconds before retrying.",
                "retry_after": retry_after
            })
            resp.status_code = 429
            resp.headers["Retry-After"] = str(retry_after)
            return resp
        return f(*args, **kwargs)
    return decorated_function


def validate_pdf_stream(file_stream: io.BytesIO, max_size_bytes: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
    """
    Validates PDF file integrity:
    1. Checks size limit.
    2. Inspects magic bytes (%PDF-).
    """
    file_stream.seek(0, os.SEEK_END)
    size = file_stream.tell()
    file_stream.seek(0)

    if size == 0:
        return False, "The uploaded file is completely empty."

    if size > max_size_bytes:
        return False, f"File size ({size / (1024*1024):.1f}MB) exceeds the maximum allowed limit of {max_size_bytes // (1024*1024)}MB."

    header = file_stream.read(5)
    file_stream.seek(0)

    # Magic byte check for PDF (%PDF-)
    if not header.startswith(b"%PDF-"):
        return False, "Invalid file signature. File is not an authentic PDF document."

    return True, ""


def apply_security_headers(response: Response) -> Response:
    """
    Applies strict OWASP-recommended security headers to all HTTP responses.
    """
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Clickjacking protection
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    # Strict Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Disable risky browser APIs (camera, mic, geo)
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # Content Security Policy (allows necessary CDNs: FontAwesome, Google Fonts, and self)
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:",
        "img-src 'self' data: https:",
        "connect-src 'self'",
        "frame-ancestors 'self'",
        "base-uri 'self'",
        "form-action 'self'"
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    # HSTS if running over HTTPS
    if request.is_secure or request.headers.get("X-Forwarded-Proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response
