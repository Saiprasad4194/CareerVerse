"""
Regression Tests to Verify Zero Disruptions to Existing CareerVerse AI Features.
"""

import unittest
from app import app, validate_career_input
from salary_data_layer import get_verified_salary_data


class TestExistingFunctionality(unittest.TestCase):
    """Ensures existing routes, career validation, templates, and salary layers are 100% intact."""

    def setUp(self):
        self.client = app.test_client()

    def test_pages_render_successfully(self):
        routes = [
            "/",
            "/generate",
            "/about",
            "/privacy",
            "/terms",
            "/support",
            "/ai-tools",
            "/career-intelligence",
            "/career-chat",
            "/resume",
            "/skill-gap",
            "/career-reality",
            "/career-match",
            "/compare",
            "/salary-predictor",
            "/col-calculator"
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, f"Route {route} failed to load")

    def test_career_input_validation(self):
        # Valid careers
        is_valid, _ = validate_career_input("Data Scientist")
        self.assertTrue(is_valid)

        is_valid, _ = validate_career_input("Software Engineer")
        self.assertTrue(is_valid)

        # Invalid careers (gibberish or prompt injection attempts)
        is_valid, err = validate_career_input("asdfghjklqwerty")
        self.assertFalse(is_valid)

        is_valid, err = validate_career_input("a")
        self.assertFalse(is_valid)

    def test_col_calculator_api(self):
        response = self.client.post("/col-calculator-api", json={
            "base_salary": "600,000",
            "base_country": "India",
            "target_country": "Ireland",
            "career": "Data Analyst",
            "experience": "Entry Level",
            "target_city": "Dublin"
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["base_currency_code"], "INR")
        self.assertEqual(data["target_currency_code"], "EUR")
        self.assertIn("currency_conversion", data)
        self.assertIn("ppp_comparison", data)
        self.assertIn("market_salary", data)

    def test_verified_salary_data_layer(self):
        data = get_verified_salary_data(
            career="Software Engineer",
            country="India",
            experience_years=3
        )
        self.assertTrue(data["career_valid"])
        self.assertTrue(data["country_valid"])
        self.assertIn("salary", data)
        self.assertIn("currency", data)
        self.assertEqual(data["currency"]["code"], "INR")
        self.assertIn("min", data["salary"])
        self.assertIn("max", data["salary"])
        self.assertIn("median", data["salary"])


if __name__ == "__main__":
    unittest.main()
