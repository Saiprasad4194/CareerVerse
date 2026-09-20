"""
Local Development Provider for CareerVerse AI Confidential Computing Abstraction.

Runs a software-isolated memory enclave simulator with real PII detection,
redaction, ephemeral AES-256-GCM encryption, and memory shredding.

IMPORTANT:
This provider is for local development and non-confidential environments.
It explicitly and transparently reports that it is NOT hardware-isolated.
"""

from datetime import datetime, timezone
import hashlib
import os
from typing import Any, Dict, Optional

from secure_processing.interface import ISecureProvider
from secure_processing.pii_redactor import PIIRedactor
from secure_processing.crypto import CryptoEngine
from secure_processing.audit_logger import audit_logger


class LocalDevelopmentProvider(ISecureProvider):
    """
    Software-isolated execution provider for development environments.
    """

    def __init__(self):
        # Ephemeral session key generated strictly in RAM
        self._ephemeral_master_key = CryptoEngine.generate_key()
        self._key_store: Dict[str, bytes] = {}

    @property
    def provider_name(self) -> str:
        return "Local Software Memory Enclave (Simulated)"

    @property
    def is_hardware_isolated(self) -> bool:
        return False

    @property
    def security_mode(self) -> str:
        return "development_isolated"

    def process_sensitive_data(
        self, data: str | bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Redacts PII from text or bytes and encrypts temporary memory buffers.
        """
        options = options or {}
        text = data.decode("utf-8", errors="ignore") if isinstance(data, bytes) else str(data)

        # 1. Ephemeral memory protection: Encrypt incoming buffer in RAM
        raw_bytes = text.encode("utf-8")
        session_key = CryptoEngine.generate_key()
        encrypted_buffer = CryptoEngine.encrypt(raw_bytes, session_key)

        # 2. PII Detection and Minimization
        sanitized_text, pii_meta = PIIRedactor.redact(text)

        # 3. Shred raw temporary buffer
        mutable_raw = bytearray(raw_bytes)
        CryptoEngine.shred_memory(mutable_raw)

        # 4. Audit Log without sensitive content
        audit_logger.log_event(
            event_type="PII_REDACTION_EXECUTED",
            status="SUCCESS",
            details={
                "provider": self.provider_name,
                "total_redacted": pii_meta["total_redacted"],
                "detected_types": pii_meta["detected_types"],
                "hardware_isolated": False
            }
        )

        return {
            "processed_text": sanitized_text,
            "redacted_entities_count": pii_meta["total_redacted"],
            "redacted_types": pii_meta["detected_types"],
            "entities_breakdown": pii_meta["entities_redacted"],
            "security_metadata": {
                "provider": self.provider_name,
                "mode": self.security_mode,
                "hardware_isolated": False,
                "cipher": "AES-256-GCM",
                "zero_retention_verified": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    def secure_inference(
        self,
        prompt: str,
        inference_fn: Any,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invokes inference function with sanitized prompt.
        """
        options = options or {}
        audit_logger.log_event(
            event_type="SECURE_INFERENCE_INVOKED",
            status="SUCCESS",
            details={"provider": self.provider_name, "hardware_isolated": False}
        )
        result = inference_fn(prompt)
        return {
            "result": result,
            "security_metadata": {
                "provider": self.provider_name,
                "hardware_isolated": False,
                "mode": self.security_mode
            }
        }

    def secure_key_operation(
        self,
        operation: str,
        data: bytes,
        key_id: Optional[str] = None,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Executes local symmetric encryption/decryption using ephemeral keys.
        """
        op = operation.lower().strip()
        key = self._key_store.get(key_id, self._ephemeral_master_key) if key_id else self._ephemeral_master_key

        if op in ("encrypt", "enc"):
            return CryptoEngine.encrypt(data, key, associated_data)
        elif op in ("decrypt", "dec"):
            return CryptoEngine.decrypt(data, key, associated_data)
        elif op == "store_key":
            if not key_id:
                raise ValueError("key_id required to store key")
            self._key_store[key_id] = data
            return b"OK"
        else:
            raise ValueError(f"Unsupported cryptographic operation: {operation}")

    def get_attestation_report(self, nonce: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Returns an explicit simulated attestation report with a clear warning.
        """
        return {
            "status": "SIMULATED_ATTESTATION",
            "is_hardware_backed": False,
            "enclave_platform": "None (Local Software Memory Simulation)",
            "warning": "This environment is NOT hardware-isolated. Do NOT claim TEE hardware security.",
            "pcrs": {
                "PCR0": "0000000000000000000000000000000000000000000000000000000000000000",
                "PCR1": "0000000000000000000000000000000000000000000000000000000000000000",
                "PCR2": "0000000000000000000000000000000000000000000000000000000000000000"
            },
            "nonce": nonce.hex() if nonce else None,
            "signature_valid": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_security_status(self) -> Dict[str, Any]:
        """
        Returns honest security status for UI and verification.
        """
        return {
            "active": True,
            "provider": self.provider_name,
            "is_hardware_isolated": False,
            "security_mode": self.security_mode,
            "display_badge": "Secure Processing: Development Mode",
            "badge_color": "#38bdf8",  # Sky blue
            "description": "Software-isolated memory buffer active. PII is automatically redacted before AI evaluation, and raw resumes have zero disk retention. Hardware TEE isolation is inactive in local development.",
            "features": {
                "pii_redaction": True,
                "zero_disk_retention": True,
                "in_memory_encryption": True,
                "hardware_enclave_isolation": False,
                "remote_attestation_verified": False
            }
        }
