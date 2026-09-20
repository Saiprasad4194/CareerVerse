"""
Security Provider Manager and Factory for CareerVerse AI.

Orchestrates initialization and lifecycle of confidential computing providers.
Provides a unified, dependency-injected API so application routes remain decoupled
from underlying hardware mechanisms.
"""

import os
from typing import Any, Dict, Optional

from secure_processing.interface import ISecureProvider
from secure_processing.local_provider import LocalDevelopmentProvider
from secure_processing.tee_provider import NitroEnclaveProvider
from secure_processing.audit_logger import audit_logger


_ACTIVE_PROVIDER: Optional[ISecureProvider] = None


def get_secure_provider() -> ISecureProvider:
    """
    Returns the singleton ISecureProvider instance based on environment configuration.
    
    Configuration (via SECURITY_MODE env var):
      - 'auto' (default): Automatically probes for hardware TEE; falls back cleanly to local.
      - 'tee_enclave' | 'hardware_tee': Configures AWS Nitro Enclave / hardware TEE provider.
      - 'local_dev' | 'development': Configures software-isolated local provider.
    """
    global _ACTIVE_PROVIDER
    if _ACTIVE_PROVIDER is not None:
        return _ACTIVE_PROVIDER

    mode = os.getenv("SECURITY_MODE", "auto").strip().lower()

    if mode in ("tee_enclave", "hardware_tee", "nitro"):
        _ACTIVE_PROVIDER = NitroEnclaveProvider(auto_fallback=True)
    elif mode in ("local_dev", "development", "local"):
        _ACTIVE_PROVIDER = LocalDevelopmentProvider()
    else:  # 'auto'
        # Probe TEE provider; if hardware is detected, use it; otherwise use local provider
        tee_candidate = NitroEnclaveProvider(auto_fallback=True)
        if tee_candidate.is_hardware_isolated:
            _ACTIVE_PROVIDER = tee_candidate
        else:
            _ACTIVE_PROVIDER = LocalDevelopmentProvider()

    audit_logger.log_event(
        event_type="SECURITY_PROVIDER_INITIALIZED",
        status="SUCCESS",
        details={
            "provider_name": _ACTIVE_PROVIDER.provider_name,
            "security_mode": _ACTIVE_PROVIDER.security_mode,
            "is_hardware_isolated": _ACTIVE_PROVIDER.is_hardware_isolated,
        }
    )

    return _ACTIVE_PROVIDER


def set_secure_provider(provider: ISecureProvider) -> None:
    """Explicitly injects a provider (useful for unit testing)."""
    global _ACTIVE_PROVIDER
    _ACTIVE_PROVIDER = provider


def process_sensitive_data(data: str | bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience proxy to active provider."""
    return get_secure_provider().process_sensitive_data(data, options)


def secure_inference(prompt: str, inference_fn: Any, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience proxy to active provider."""
    return get_secure_provider().secure_inference(prompt, inference_fn, options)


def secure_key_operation(
    operation: str, data: bytes, key_id: Optional[str] = None, associated_data: Optional[bytes] = None
) -> bytes:
    """Convenience proxy to active provider."""
    return get_secure_provider().secure_key_operation(operation, data, key_id, associated_data)


def get_security_status() -> Dict[str, Any]:
    """Convenience proxy to retrieve active security status."""
    return get_secure_provider().get_security_status()


def get_attestation_report(nonce: Optional[bytes] = None) -> Dict[str, Any]:
    """Convenience proxy to retrieve attestation report."""
    return get_secure_provider().get_attestation_report(nonce)
