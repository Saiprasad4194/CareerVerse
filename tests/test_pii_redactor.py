"""
Unit Tests for PII Detection, Minimization, and Redaction Engine.
"""

import unittest
from secure_processing.pii_redactor import PIIRedactor


class TestPIIRedactor(unittest.TestCase):
    """Verifies PII detection precision and technical competency preservation."""

    def test_email_redaction(self):
        sample = "Contact me at rahul.sharma99@gmail.com or john.doe@work.co.uk for inquiries."
        sanitized, meta = PIIRedactor.redact(sample)
        self.assertNotIn("rahul.sharma99@gmail.com", sanitized)
        self.assertNotIn("john.doe@work.co.uk", sanitized)
        self.assertIn("[REDACTED_EMAIL]", sanitized)
        self.assertEqual(meta["entities_redacted"]["EMAIL"], 2)

    def test_phone_redaction(self):
        sample = "Call me at +91 9876543210 or (555) 123-4567 or 98765 43210."
        sanitized, meta = PIIRedactor.redact(sample)
        self.assertNotIn("9876543210", sanitized)
        self.assertNotIn("555", sanitized)
        self.assertIn("[REDACTED_PHONE]", sanitized)
        self.assertGreaterEqual(meta["entities_redacted"]["PHONE"], 2)

    def test_government_id_redaction(self):
        sample = "Aadhaar: 1234 5678 9012, PAN: ABCDE1234F, SSN: 123-45-6789."
        sanitized, meta = PIIRedactor.redact(sample)
        self.assertNotIn("1234 5678 9012", sanitized)
        self.assertNotIn("ABCDE1234F", sanitized)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertIn("[REDACTED_AADHAAR]", sanitized)
        self.assertIn("[REDACTED_PAN]", sanitized)
        self.assertIn("[REDACTED_SSN]", sanitized)

    def test_candidate_name_redaction(self):
        sample = """Rahul Sharma
Email: rahul@gmail.com
Phone: +91 9876543210
Senior Full Stack Engineer
B.Tech in Computer Science and Engineering"""
        sanitized, meta = PIIRedactor.redact(sample)
        self.assertNotIn("Rahul Sharma", sanitized)
        self.assertIn("[REDACTED_NAME]", sanitized)
        self.assertIn("[REDACTED_EMAIL]", sanitized)
        self.assertIn("[REDACTED_PHONE]", sanitized)
        # Verify career context is fully preserved
        self.assertIn("Senior Full Stack Engineer", sanitized)
        self.assertIn("B.Tech in Computer Science and Engineering", sanitized)

    def test_competency_and_metric_preservation(self):
        """Ensures that technical skills, frameworks, metrics, and years are NOT stripped."""
        sample = """
PROFESSIONAL EXPERIENCE:
Software Engineer at TechCorp (2021 - 2024)
- Built high-performance microservices using Python, Go, and Docker on AWS.
- Decreased API latency by 45% for 2.5M daily active users.
- Maintained 99.99% system uptime and scaled PostgreSQL database sharding.
- Implemented CI/CD pipelines with GitHub Actions and Kubernetes.
- Education: B.Tech CSE with 8.9 CGPA.
"""
        sanitized, meta = PIIRedactor.redact(sample)
        self.assertIn("Python", sanitized)
        self.assertIn("Go", sanitized)
        self.assertIn("Docker", sanitized)
        self.assertIn("AWS", sanitized)
        self.assertIn("PostgreSQL", sanitized)
        self.assertIn("Kubernetes", sanitized)
        self.assertIn("45%", sanitized)
        self.assertIn("2.5M", sanitized)
        self.assertIn("99.99%", sanitized)
        self.assertIn("8.9 CGPA", sanitized)

    def test_empty_and_whitespace_input(self):
        sanitized, meta = PIIRedactor.redact("   \n\t  ")
        self.assertEqual(sanitized, "")
        self.assertEqual(meta["total_redacted"], 0)


if __name__ == "__main__":
    unittest.main()
