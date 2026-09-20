"""
Unit Tests for Secure Processing Layer & Provider Abstractions.
"""

import os
import unittest
from secure_processing.interface import ISecureProvider
from secure_processing.local_provider import LocalDevelopmentProvider
from secure_processing.tee_provider import NitroEnclaveProvider
from secure_processing.manager import (
    get_secure_provider,
    set_secure_provider,
    process_sensitive_data,
    get_security_status,
    get_attestation_report
)


class TestSecureProcessingLayer(unittest.TestCase):
    """Verifies confidential computing provider abstraction and honest status reporting."""

    def setUp(self):
        self.local_prov = LocalDevelopmentProvider()

    def test_local_provider_implements_interface(self):
        self.assertIsInstance(self.local_prov, ISecureProvider)
        self.assertFalse(self.local_prov.is_hardware_isolated)
        self.assertEqual(self.local_prov.security_mode, "development_isolated")

    def test_local_provider_process_sensitive_data(self):
        sample = "John Doe\nEmail: john@gmail.com\nPhone: 9876543210\nSenior React Developer"
        result = self.local_prov.process_sensitive_data(sample)

        self.assertIn("processed_text", result)
        self.assertNotIn("john@gmail.com", result["processed_text"])
        self.assertNotIn("9876543210", result["processed_text"])
        self.assertIn("Senior React Developer", result["processed_text"])
        self.assertFalse(result["security_metadata"]["hardware_isolated"])
        self.assertTrue(result["security_metadata"]["zero_retention_verified"])

    def test_honest_security_status_reporting(self):
        status = self.local_prov.get_security_status()
        self.assertIn("Secure Processing: Development Mode", status["display_badge"])
        self.assertFalse(status["is_hardware_isolated"])
        self.assertFalse(status["features"]["hardware_enclave_isolation"])
        self.assertTrue(status["features"]["pii_redaction"])
        self.assertTrue(status["features"]["zero_disk_retention"])

    def test_attestation_report_honest_warning(self):
        report = self.local_prov.get_attestation_report(nonce=b"test_nonce_123")
        self.assertEqual(report["status"], "SIMULATED_ATTESTATION")
        self.assertFalse(report["is_hardware_backed"])
        self.assertIn("NOT hardware-isolated", report["warning"])
        self.assertEqual(report["nonce"], b"test_nonce_123".hex())

    def test_nitro_enclave_fallback(self):
        """When hardware enclave is unreachable, NitroEnclaveProvider cleanly falls back."""
        tee_prov = NitroEnclaveProvider(auto_fallback=True)
        # On Windows dev machine, hardware vsock is not present
        self.assertFalse(tee_prov.is_hardware_isolated)
        sample = "Alice Smith\nEmail: alice@example.com\nData Scientist"
        res = tee_prov.process_sensitive_data(sample)
        self.assertNotIn("alice@example.com", res["processed_text"])
        self.assertIn("Data Scientist", res["processed_text"])

    def test_manager_singleton_and_injection(self):
        custom_prov = LocalDevelopmentProvider()
        set_secure_provider(custom_prov)
        self.assertIs(get_secure_provider(), custom_prov)


if __name__ == "__main__":
    unittest.main()
