"""
Unit Tests for Hackathon Innovative AI Features:
- Job Description Intelligence (Required vs Preferred, Experience, Clarity Score)
- Learning Recommender & Skill Gap Roadmaps
- Profile Fact Extractor (Degrees, Experience, Fact vs Inference Tagging)
"""

import unittest
from src.jd_analyzer import analyze_job_description
from src.learning_recommender import get_recommendations_for_missing_skills
from src.profile_extractor import extract_candidate_profile_facts, categorize_explanation_elements


class TestInnovativeFeatures(unittest.TestCase):
    """Test suite for hackathon AI features."""

    def test_jd_intelligence_analyzer(self):
        """Verifies skill requirement splitting, experience extraction, and clarity audit."""
        jd = (
            "We are seeking an AI Engineer to join our team.\n\n"
            "Requirements:\n"
            "- Strong proficiency in Python, PyTorch, and Docker.\n"
            "- 3+ years of relevant industry experience.\n"
            "- Bachelor's degree in Computer Science.\n\n"
            "Preferred Qualifications:\n"
            "- Familiarity with Kubernetes, FastAPI, and GCP.\n"
        )
        analysis = analyze_job_description(jd)
        self.assertIn("Python", analysis["required_skills"])
        self.assertIn("Docker", analysis["required_skills"])
        self.assertIn("Kubernetes", analysis["preferred_skills"])
        self.assertIn("3+", analysis["experience_required"])
        self.assertIn("Bachelor's Degree", analysis["education_required"])
        self.assertGreaterEqual(analysis["clarity_score"], 70)

    def test_learning_recommender(self):
        """Verifies that missing skills return actionable learning roadmaps."""
        missing = ["Kubernetes", "PyTorch", "Rust"]
        roadmaps = get_recommendations_for_missing_skills(missing)
        self.assertEqual(len(roadmaps), 3)
        k8s_roadmap = roadmaps[0]
        self.assertIn("Pods", str(k8s_roadmap["key_concepts"]))
        self.assertIn("project_idea", k8s_roadmap)
        self.assertIn("estimated_time", k8s_roadmap)

    def test_profile_fact_extractor(self):
        """Verifies extraction of degrees, experience spans, and fact vs inference separation."""
        resume_text = (
            "Jane Doe\n"
            "Senior Machine Learning Engineer\n"
            "Education: Bachelor of Technology (B.Tech) in Computer Science, 2018 - 2022.\n"
            "Experience: 4+ years of professional software experience developing PyTorch models.\n"
            "Certifications: AWS Certified Solutions Architect, CKA Kubernetes Administrator."
        )
        facts = extract_candidate_profile_facts(resume_text)
        self.assertEqual(len(facts["degrees"]), 1)
        self.assertEqual(facts["degrees"][0]["level"], "Bachelor's Degree")
        self.assertEqual(facts["years_of_experience_est"], 4.0)
        self.assertIn("AWS Certified Solutions Architect", str(facts["certifications"]))

        # Fact vs Inference categorization
        dummy_explanation = {
            "score_breakdown": {"semantic_score_pct": 82.5, "skill_match_pct": 75.0},
            "overall_fit": "Strong Match"
        }
        categorized = categorize_explanation_elements(dummy_explanation, facts)
        self.assertTrue(len(categorized["extracted_facts"]) >= 2)
        self.assertTrue(len(categorized["model_inferences"]) >= 2)


if __name__ == "__main__":
    unittest.main()
