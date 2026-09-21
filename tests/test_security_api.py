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


    def test_resume_upload_valid_pdf_success_with_fallback(self):
        valid_pdf_bytes = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page
   /Parent 2 0 R
   /MediaBox [0 0 612 792]
   /Resources << /Font << /F1 4 0 R >> >>
   /Contents 5 0 R
>>
endobj
4 0 obj
<< /Type /Font
   /Subtype /Type1
   /BaseFont /Helvetica
>>
endobj
5 0 obj
<< /Length 73 >>
stream
BT
/F1 12 Tf
72 712 Td
(Alice Smith - Senior Software Engineer Python React Docker) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000332 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
455
%%EOF
"""
        data = {
            "resume": (io.BytesIO(valid_pdf_bytes), "alice_resume.pdf"),
            "target_role": "Software Engineer"
        }
        response = self.client.post("/resume-api", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        res = response.get_json()
        self.assertTrue(res["success"])
        self.assertIn("data", res)
        self.assertIn("ats_score", res)
        self.assertIn("Python", res.get("extracted_skills", []))
        self.assertIn("React", res.get("extracted_skills", []))
        self.assertIn("Docker", res.get("extracted_skills", []))


if __name__ == "__main__":
    unittest.main()
