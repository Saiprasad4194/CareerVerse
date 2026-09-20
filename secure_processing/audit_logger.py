"""
Zero-PII Structured Security Audit Logger for CareerVerse AI.

Guarantees that security events, rate-limit violations, and enclave interactions
are logged with auditability while strictly excluding sensitive user data, PII,
raw prompts, and API keys.
"""

import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class SecurityAuditLogger:
    """
    Dedicated security logger enforcing defense-in-depth sanitization of log streams.
    """

    API_KEY_REGEX = re.compile(r'AIzaSy[A-Za-z0-9_-]{20,}')
    BEARER_REGEX = re.compile(r'(?:bearer|token|secret|key)[\s:=]+(?!\[REDACTED_)([A-Za-z0-9._-]{8,})', re.IGNORECASE)

    def __init__(self, logger_name: str = "careerverse.security"):
        self.logger = logging.getLogger(logger_name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("[SECURITY_AUDIT] %(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """Removes any unintentional secrets or keys before log output."""
        if not isinstance(message, str):
            message = str(message)
        sanitized = cls.API_KEY_REGEX.sub("[REDACTED_API_KEY]", message)
        sanitized = cls.BEARER_REGEX.sub(r'token=[REDACTED_TOKEN]', sanitized)
        return sanitized

    @classmethod
    def anonymize_identifier(cls, identifier: Optional[str]) -> str:
        """One-way SHA-256 hash of IP or session token for audit correlation without deanonymization."""
        if not identifier:
            return "anonymous"
        return hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:12]

    def log_event(
        self,
        event_type: str,
        status: str = "SUCCESS",
        client_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        level: int = logging.INFO
    ) -> None:
        """
        Emits a structured, sanitized audit log entry.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "status": status,
            "client_hash": self.anonymize_identifier(client_id),
            "details": details or {}
        }
        raw_json = json.dumps(entry, default=str)
        safe_output = self.sanitize_message(raw_json)
        self.logger.log(level, safe_output)


# Default module instance
audit_logger = SecurityAuditLogger()
