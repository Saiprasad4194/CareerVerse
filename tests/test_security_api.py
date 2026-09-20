"""
Integration Tests for CareerVerse Security Architecture, APIs, and Middleware.
"""

import io
import json
import unittest
from unittest.mock import patch

from app import app, handle_gemini_error
from secure_processing.middleware import sensitive_rate_limiter, validate_pdf_stream
from secure_processing.audit_logger import audit_logger


class TestSecurityAPI(unittest.TestCase):
    """Verifies security headers, endpoints, rate limiting, and upload safeguards."""

    def setUp(self):
        self.client = app.test_client()

    def test_security_headers_present(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(response.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertIn("default-src 'self'", response.headers.get("Content-Security-Policy"))

    def test_security_status_endpoint(self):
        response = self.client.get("/api/security-status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        sec = data["security"]
        self.assertIn("display_badge", sec)
        self.assertIn("Secure Processing: Development Mode", sec["display_badge"])
        self.assertFalse(sec["is_hardware_isolated"])
        self.assertTrue(sec["features"]["pii_redaction"])
        self.assertTrue(sec["features"]["zero_disk_retention"])

    def test_security_attestation_endpoint(self):
        response = self.client.get("/api/security-attestation?nonce=nonce_test_456")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        att = data["attestation"]
        self.assertEqual(att["status"], "SIMULATED_ATTESTATION")
        self.assertFalse(att["is_hardware_backed"])
        self.assertIn("warning", att)

    def test_magic_byte_pdf_validation(self):
        # Fake PDF: text file with .pdf extension
        fake_stream = io.BytesIO(b"Hello world, I am not a real PDF!")
        valid, err = validate_pdf_stream(fake_stream)
        self.assertFalse(valid)
        self.assertIn("Invalid file signature", err)

        # Real PDF signature
        valid_stream = io.BytesIO(b"%PDF-1.5 fake pdf content structure here")
        valid, err = validate_pdf_stream(valid_stream)
        self.assertTrue(valid)

    def test_resume_upload_rejection_for_non_pdf(self):
        # Uploading a text file renamed to .txt
        data = {
            "resume": (io.BytesIO(b"Just text"), "resume.txt")
        }
        response = self.client.post("/resume-api", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only PDF files are allowed", response.get_json()["error"])

    def test_resume_upload_rejection_for_fake_pdf_signature(self):
        # File has .pdf extension but lacks %PDF- header
        data = {
            "resume": (io.BytesIO(b"Malicious fake executable payload"), "exploit.pdf")
        }
        response = self.client.post("/resume-api", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file signature", response.get_json()["error"])

    def test_gemini_error_sanitization_prevents_secret_leak(self):
        # Simulate an exception containing an API key
        fake_exc = Exception("Upstream failure occurred: AIzaSyD9876543210FakeKeyAtGoogleCloud on server /var/www/careerverse/app.py")
        with app.app_context():
            resp, code = handle_gemini_error(fake_exc)
            body = resp.get_json()
            self.assertFalse(body["success"])
            # Must NOT contain the API key
            self.assertNotIn("AIzaSyD9876543210FakeKeyAtGoogleCloud", body["error"])
            self.assertNotIn("/var/www/careerverse", body["error"])

    def test_audit_logger_sanitizes_api_keys(self):
        msg = "Call failed with key AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
        clean = audit_logger.sanitize_message(msg)
        self.assertNotIn("AIzaSy", clean)
        self.assertIn("[REDACTED_API_KEY]", clean)


if __name__ == "__main__":
    unittest.main()
