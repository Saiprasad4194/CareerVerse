"""
Secure Processing Interface Definition for CareerVerse AI.

Defines the contract for confidential computing / Trusted Execution Environment (TEE)
providers. Normal application code interacts strictly with this interface, remaining
agnostic to whether sensitive operations execute locally or inside a hardware enclave.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class ISecureProvider(ABC):
    """
    Abstract Base Class defining the contract for all secure execution providers.
    
    Implementations must handle:
    - Sensitive data processing (PII minimization, redaction, sanitization)
    - Cryptographic key operations (encryption, decryption, key derivation)
    - Secure inference orchestration (dispatching sanitized prompts to AI)
    - Hardware attestation reporting (cryptographic proof of execution environment)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name (e.g., 'Local Memory Enclave', 'AWS Nitro Enclave')."""
        pass

    @property
    @abstractmethod
    def is_hardware_isolated(self) -> bool:
        """True ONLY if backed by authentic hardware TEE (AMD SEV-SNP, Intel SGX/TDX, AWS Nitro)."""
        pass

    @property
    @abstractmethod
    def security_mode(self) -> str:
        """Mode identifier: 'development_isolated' | 'hardware_tee' | 'confidential_vm'."""
        pass

    @abstractmethod
    def process_sensitive_data(
        self, data: str | bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process sensitive user input (e.g. resume text or PDF stream).
        Performs PII detection, redaction, and minimization.
        
        Returns:
            Dict containing:
                - 'processed_text': Sanitized text safe for external AI processing.
                - 'redacted_entities_count': Total number of PII entities scrubbed.
                - 'redacted_types': List of entity types identified (e.g. ['EMAIL', 'PHONE']).
                - 'security_metadata': Integrity checksums, session IDs, and zero-retention confirmation.
        """
        pass

    @abstractmethod
    def secure_inference(
        self,
        prompt: str,
        inference_fn: Any,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes AI inference with sanitized payloads, ensuring secrets and PII are never leaked.
        """
        pass

    @abstractmethod
    def secure_key_operation(
        self,
        operation: str,
        data: bytes,
        key_id: Optional[str] = None,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Perform cryptographic operations (encrypt, decrypt, sign, hash).
        Keys remain isolated inside the provider memory boundary.
        """
        pass

    @abstractmethod
    def get_attestation_report(self, nonce: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Returns cryptographic attestation report confirming enclave measurements (PCRs)
        and signing authority. If local/simulated, explicitly flags non-hardware status.
        """
        pass

    @abstractmethod
    def get_security_status(self) -> Dict[str, Any]:
        """
        Returns status dictionary for UI indicator and audit verification.
        Guarantees 100% technical accuracy with zero false TEE claims.
        """
        pass
