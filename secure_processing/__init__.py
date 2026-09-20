"""
CareerVerse AI Secure Processing & Confidential Computing Package.

Exports core provider abstraction, PII redactor, security middleware, and audit logger.
"""

from secure_processing.interface import ISecureProvider
from secure_processing.crypto import CryptoEngine
from secure_processing.pii_redactor import PIIRedactor
from secure_processing.local_provider import LocalDevelopmentProvider
from secure_processing.tee_provider import NitroEnclaveProvider
from secure_processing.manager import (
    get_secure_provider,
    set_secure_provider,
    process_sensitive_data,
    secure_inference,
    secure_key_operation,
    get_security_status,
    get_attestation_report,
)
from secure_processing.audit_logger import audit_logger, SecurityAuditLogger
from secure_processing.middleware import (
    rate_limit_sensitive,
    apply_security_headers,
    validate_pdf_stream,
    sensitive_rate_limiter,
)

__all__ = [
    "ISecureProvider",
    "CryptoEngine",
    "PIIRedactor",
    "LocalDevelopmentProvider",
    "NitroEnclaveProvider",
    "get_secure_provider",
    "set_secure_provider",
    "process_sensitive_data",
    "secure_inference",
    "secure_key_operation",
    "get_security_status",
    "get_attestation_report",
    "audit_logger",
    "SecurityAuditLogger",
    "rate_limit_sensitive",
    "apply_security_headers",
    "validate_pdf_stream",
    "sensitive_rate_limiter",
]
