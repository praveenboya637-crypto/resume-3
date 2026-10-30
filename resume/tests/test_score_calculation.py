"""
AI Resume Screening and Job Matching System
Dedicated Unit Tests for Score Calculation, Weights, Bounds, and Synonym Consistency.
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.constants import DEFAULT_MODEL_NAME, SAMPLE_JOB_DESCRIPTIONS
from src.embeddings import load_sentence_transformer_model, batch_compute_similarity, compute_semantic_similarity
from src.skills_extractor import extract_skills_from_text, analyze_skill_gap, extract_skill_evidence
from src.ranker import rank_resumes, generate_explainable_feedback


class TestScoreCalculation(unittest.TestCase):
    """Exhaustive tests for composite score calculation, weights, and consistency."""

    @classmethod
    def setUpClass(cls):
        cls.model, cls.backend = load_sentence_transformer_model(DEFAULT_MODEL_NAME)
        cls.sample_jd = (
            "Looking for an AI Engineer with strong proficiency in Python, PyTorch, "
            "Docker, Kubernetes, and FastAPI to build machine learning microservices."
        )
        cls.sample_resume = (
            "Senior AI Engineer with 4 years experience. "
            "Developed machine learning models using Python and PyTorch. "
            "Deployed containerized microservices using Docker, Kubernetes, and FastAPI."
        )

    def test_composite_score_formula_varying_weights(self):
        """Verifies exact composite score formula across different user-configured weights."""
        resumes = [{"filename": "cand.pdf", "clean_text": self.sample_resume, "status": "success"}]
        sims = batch_compute_similarity(resumes, self.sample_jd, model=self.model)
        sem_pct = round(sims[0] * 100, 1)

        gap = analyze_skill_gap(self.sample_resume, self.sample_jd)
        skill_pct = gap["skill_match_percentage"]

        weight_pairs = [
            (0.50, 0.50),
            (0.60, 0.40),
            (0.70, 0.30),
            (0.80, 0.20),
            (1.00, 0.00),
            (0.00, 1.00)
        ]

        for w_sem, w_ski in weight_pairs:
            ranked, _ = rank_resumes(
                parsed_resumes=resumes,
                jd_text=self.sample_jd,
                semantic_similarities=sims,
                semantic_weight=w_sem,
                skill_weight=w_ski
            )
            cand = ranked[0]
            expected = round((sem_pct * w_sem) + (skill_pct * w_ski), 1)
            self.assertEqual(
                cand["composite_score"],
                expected,
                f"Mismatch for weights ({w_sem}, {w_ski}): got {cand['composite_score']}, expected {expected}"
            )
            # Verify formula string in explanation
            bdown = cand["explanation"]["score_breakdown"]
            self.assertIn(f"{cand['composite_score']:.1f}%", bdown["formula"])

    def test_score_bounds_and_clamping(self):
        """Ensures composite scores are strictly bounded within [0.0, 100.0]."""
        resumes = [
            {"filename": "empty.pdf", "clean_text": "", "status": "error"},
            {"filename": "perfect.pdf", "clean_text": self.sample_jd, "status": "success"}
        ]
        sims = [0.0, 1.0]
        ranked, _ = rank_resumes(resumes, self.sample_jd, sims)

        for c in ranked:
            self.assertGreaterEqual(c["composite_score"], 0.0)
            self.assertLessEqual(c["composite_score"], 100.0)

    def test_single_vs_multiple_resume_consistency(self):
        """Verifies that analyzing a resume individually yields identical results to batch analysis."""
        res_a = {"filename": "a.pdf", "clean_text": self.sample_resume, "status": "success"}
        res_b = {"filename": "b.docx", "clean_text": "Web developer with JavaScript, React, and CSS.", "status": "success"}

        # 1. Individual analysis of res_a
        sim_single = batch_compute_similarity([res_a], self.sample_jd, model=self.model)
        ranked_single, _ = rank_resumes([res_a], self.sample_jd, sim_single, semantic_weight=0.60, skill_weight=0.40)
        score_single = ranked_single[0]["composite_score"]

        # 2. Batch analysis of [res_a, res_b]
        sim_batch = batch_compute_similarity([res_a, res_b], self.sample_jd, model=self.model)
        ranked_batch, _ = rank_resumes([res_a, res_b], self.sample_jd, sim_batch, semantic_weight=0.60, skill_weight=0.40)
        cand_a_batch = next(c for c in ranked_batch if c["candidate_name"] == "a.pdf")
        score_batch = cand_a_batch["composite_score"]

        self.assertEqual(score_single, score_batch, "Individual score diverged from batch score!")

    def test_synonym_unification_impact_on_score(self):
        """Verifies that synonym variations (e.g. K8s for Kubernetes, Postgres for PostgreSQL) match accurately."""
        jd_with_canonical = "Required: Kubernetes, PostgreSQL, Machine Learning, Fast-API."
        resume_with_synonyms = "Experienced in K8s clusters, Postgres database optimization, ML modeling, and FastAPI."

        gap = analyze_skill_gap(resume_with_synonyms, jd_with_canonical)
        # Should match all 4 skills through synonym canonicalization
        self.assertIn("Kubernetes", gap["matched_skills"])
        self.assertIn("PostgreSQL", gap["matched_skills"])
        self.assertIn("Machine Learning", gap["matched_skills"])
        self.assertIn("FastAPI", gap["matched_skills"])
        self.assertEqual(gap["skill_match_percentage"], 100.0)

    def test_job_description_with_zero_taxonomy_skills(self):
        """When JD contains no taxonomy skills, composite score falls back 100% to semantic similarity."""
        jd_no_tech = "We are seeking a driven leader to collaborate with executive partners and steer quarterly company growth."
        resumes = [{"filename": "cand.pdf", "clean_text": self.sample_resume, "status": "success"}]
        sims = batch_compute_similarity(resumes, jd_no_tech, model=self.model)
        ranked, _ = rank_resumes(resumes, jd_no_tech, sims, semantic_weight=0.60, skill_weight=0.40)

        cand = ranked[0]
        # Must equal semantic similarity % without crashing or division by zero
        expected_sem = round(sims[0] * 100, 1)
        self.assertEqual(cand["composite_score"], expected_sem)

    def test_verifiable_evidence_extraction(self):
        """Verifies that extract_skill_evidence retrieves verbatim text from the resume."""
        snippet = "Architected enterprise RAG system using LangChain, Hugging Face Transformers, and PyTorch."
        evidence = extract_skill_evidence(snippet, "pytorch")
        self.assertIsNotNone(evidence)
        self.assertIn("PyTorch", evidence)
        self.assertIn("LangChain", evidence)


if __name__ == "__main__":
    unittest.main()
