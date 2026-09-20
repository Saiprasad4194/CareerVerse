"""
Unit Tests for Curated Resources & Anti-Hallucination Recommendation Layer
"""

import unittest
from app import app
from curated_resources import (
    VERIFIED_PLATFORMS,
    CURATED_SKILL_RESOURCES,
    build_safe_platform_url,
    normalize_platform_name,
    get_curated_resources_for_skills,
    enrich_and_sanitize_roadmap_resources,
    enrich_and_sanitize_navigator_roadmap,
    enrich_gap_analysis_resources
)


class TestCuratedResources(unittest.TestCase):
    """Test suite ensuring all course and resource recommendations are real and non-hallucinated."""

    def setUp(self):
        self.client = app.test_client()

    def test_verified_platforms_config(self):
        """Ensure all vetted platforms have valid base URLs and search patterns."""
        self.assertIn("coursera", VERIFIED_PLATFORMS)
        self.assertIn("udemy", VERIFIED_PLATFORMS)
        self.assertIn("freecodecamp", VERIFIED_PLATFORMS)
        self.assertIn("youtube", VERIFIED_PLATFORMS)
        self.assertIn("official docs", VERIFIED_PLATFORMS)

        for plat_key, meta in VERIFIED_PLATFORMS.items():
            self.assertTrue(meta["base_url"].startswith("https://"))
            self.assertIn("{query}", meta["search_url"])

    def test_safe_platform_url_builder(self):
        """Ensure safe URL generator constructs valid URLs on approved domains without hallucination."""
        # Coursera search
        c_url = build_safe_platform_url("Coursera", "Python for Everybody")
        self.assertTrue(c_url.startswith("https://www.coursera.org/search?query="))
        self.assertIn("Python", c_url)

        # YouTube search
        yt_url = build_safe_platform_url("YouTube", "freeCodeCamp")
        self.assertTrue(yt_url.startswith("https://www.youtube.com/results?search_query="))

        # freeCodeCamp
        fcc_url = build_safe_platform_url("freeCodeCamp", "Responsive Web Design")
        self.assertTrue(fcc_url.startswith("https://www.freecodecamp.org/news/search/?query="))

        # Fallback when no platform given
        fallback_url = build_safe_platform_url("", "Machine Learning")
        self.assertTrue(fallback_url.startswith("https://www.coursera.org"))

    def test_curated_resources_lookup(self):
        """Ensure curated resources are returned for common skills and careers."""
        # Data Scientist
        ds_res = get_curated_resources_for_skills("Data Scientist", "Python, Machine Learning")
        self.assertTrue(len(ds_res["courses"]) >= 2)
        self.assertTrue(len(ds_res["documentation"]) >= 1)
        self.assertTrue(len(ds_res["youtube"]) >= 1)
        self.assertTrue(len(ds_res["certifications"]) >= 1)

        # Ensure platforms are verified
        for course in ds_res["courses"]:
            self.assertIn(normalize_platform_name(course["platform"]).lower(), VERIFIED_PLATFORMS)

    def test_enrich_and_sanitize_roadmap_resources_removes_hallucinated_urls(self):
        """Verify fake/hallucinated LLM URLs are replaced by verified platform links."""
        llm_raw_resources = {
            "courses": [
                {"name": "Deep Python 2026 Masterclass", "platform": "Coursera", "url": "https://coursera.org/fake-broken-course-1234"},
                {"name": "Udemy Fast Web Dev", "platform": "Udemy", "url": "https://udemy.com/broken-course-5678"}
            ],
            "youtube": [
                {"name": "Corey Schafer Python", "platform": "YouTube", "url": "https://youtube.com/fake-deep-link-xyz"}
            ]
        }

        sanitized = enrich_and_sanitize_roadmap_resources(llm_raw_resources, "Python Developer", "Python")

        # Must not contain the broken URLs
        for c in sanitized["courses"]:
            self.assertNotIn("fake-broken-course", c["url"])
            self.assertNotIn("broken-course", c["url"])
            self.assertTrue(c["url"].startswith("https://"))

        # Must have backfilled categories to ensure rich content
        self.assertTrue(len(sanitized["courses"]) >= 3)
        self.assertTrue(len(sanitized["documentation"]) >= 1)
        self.assertTrue(len(sanitized["youtube"]) >= 1)

    def test_enrich_and_sanitize_navigator_roadmap(self):
        """Ensure phase-level navigator roadmap resources are sanitized and augmented."""
        raw_roadmap = {
            "roadmap_title": "Data Analyst Roadmap",
            "phases": [
                {
                    "title": "Phase 1: Foundations",
                    "resources": [
                        {"name": "Invented Data Course", "platform": "Coursera", "url": "https://coursera.org/nonexistent/link"},
                        "freeCodeCamp SQL"
                    ]
                },
                {
                    "title": "Phase 2: Advanced",
                    "resources": []
                }
            ]
        }

        enriched = enrich_and_sanitize_navigator_roadmap(raw_roadmap, "Data Analyst", "SQL")
        p1 = enriched["phases"][0]
        self.assertTrue(len(p1["resources"]) >= 3)
        for r in p1["resources"]:
            self.assertIn("platform", r)
            self.assertIn("url", r)
            self.assertNotIn("nonexistent", r["url"])

    def test_enrich_gap_analysis_resources(self):
        """Ensure gap analysis resources returns curated courses and certifications."""
        gap_res = enrich_gap_analysis_resources("Software Engineer", "Python, React")
        self.assertIn("recommended_courses", gap_res)
        self.assertIn("recommended_certifications", gap_res)
        self.assertTrue(len(gap_res["recommended_courses"]) >= 2)
        self.assertTrue(len(gap_res["recommended_certifications"]) >= 1)

    def test_skill_gap_api_includes_verified_resources(self):
        """Test /skill-gap-api returns curated recommended_resources and certifications."""
        resp = self.client.post("/skill-gap-api", json={
            "career": "Data Scientist",
            "skills": "Python, SQL"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("recommended_resources", data)
        self.assertIn("recommended_certifications", data)
        self.assertTrue(len(data["recommended_resources"]) > 0)
        for r in data["recommended_resources"]:
            self.assertIn("platform", r)
            self.assertIn("url", r)
            self.assertTrue(r["url"].startswith("https://"))

    def test_fallback_roadmap_contains_sanitized_resources(self):
        """Test /roadmap fallback path has verified resources without fake URLs."""
        resp = self.client.post("/roadmap", json={
            "career": "Cybersecurity Analyst",
            "country": "United States",
            "duration": "6 months"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("resources", data)
        resources = data["resources"]
        for cat in ["courses", "documentation", "youtube", "books"]:
            self.assertIn(cat, resources)
            self.assertTrue(len(resources[cat]) >= 1)
            for item in resources[cat]:
                self.assertIn("name", item)
                self.assertIn("platform", item)
    def test_navigator_gap_api_resources(self):
        """Test /navigator-gap-api includes vetted resources and certifications."""
        resp = self.client.post("/navigator-gap-api", json={
            "profile": {
                "profileTargetRole": "Machine Learning Engineer",
                "profileName": "Alex",
                "profileExperience": "1-3 years"
            },
            "current_skills": ["Python", "TensorFlow"]
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        gap_data = data.get("data") or data
        self.assertIn("recommended_courses", gap_data)
        self.assertIn("recommended_certifications", gap_data)
        self.assertTrue(len(gap_data["recommended_courses"]) >= 1)

    def test_navigator_roadmap_api_resources(self):
        """Test /navigator-roadmap-api phase resources are sanitized with safe URLs."""
        resp = self.client.post("/navigator-roadmap-api", json={
            "profile": {
                "profileTargetRole": "Cloud Architect",
                "profileName": "Sarah",
                "profileCountry": "United States"
            },
            "current_skills": ["Linux", "AWS"]
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        roadmap_data = data.get("data") or data
        self.assertIn("phases", roadmap_data)
        for phase in roadmap_data["phases"]:
            self.assertIn("resources", phase)
            self.assertTrue(len(phase["resources"]) >= 1)
            for r in phase["resources"]:
                self.assertIn("name", r)
                self.assertIn("platform", r)
                self.assertIn("url", r)
                self.assertTrue(r["url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
