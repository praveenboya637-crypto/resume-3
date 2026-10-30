"""
AI Resume Screening and Job Matching System
Comprehensive Unit & Integration Test Suite.
Tests text parsing, skill extraction, embeddings, ranking, XAI, and edge cases.
"""

import os
import sys
import unittest
import tempfile
import pymupdf
import docx

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.constants import (
    DEFAULT_MODEL_NAME,
    SAMPLE_JOB_DESCRIPTIONS,
    ETHICAL_DISCLAIMER
)
from src.parsers import (
    clean_text,
    extract_metadata_heuristics,
    extract_text_from_pdf,
    extract_text_from_docx,
    parse_resume
)
from src.skills_extractor import (
    extract_skills_from_text,
    analyze_skill_gap
)
from src.embeddings import (
    load_sentence_transformer_model,
    compute_semantic_similarity,
    batch_compute_similarity
)
from src.ranker import (
    rank_resumes,
    generate_explainable_feedback
)
from src.utils import (
    validate_job_description,
    validate_uploaded_files,
    generate_csv_report,
    sanitize_filename,
    _sanitize_csv_cell
)


class TestTextCleaningAndMetadata(unittest.TestCase):
    """Tests for text normalization and metadata extraction heuristics."""

    def test_clean_text_normalizes_bullets_and_whitespace(self):
        raw = "• Python\r\n\t• Machine  Learning\n\n\n\n- PyTorch \u201CDeep Learning\u201D"
        cleaned = clean_text(raw)
        self.assertIn("- Python", cleaned)
        self.assertIn("- PyTorch", cleaned)
        self.assertIn('"Deep Learning"', cleaned)
        self.assertNotIn("\r", cleaned)
        self.assertNotIn("   ", cleaned)

    def test_clean_text_handles_none_and_empty(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_extract_metadata_heuristics(self):
        sample = """
        John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        LinkedIn: linkedin.com/in/johndoe-ai
        GitHub: github.com/johndoe-code
        Skilled in Python and Deep Learning.
        """
        meta = extract_metadata_heuristics(sample)
        self.assertEqual(meta["email"], "john.doe@example.com")
        self.assertIn("555", meta["phone"])
        self.assertEqual(meta["linkedin"], "linkedin.com/in/johndoe-ai")
        self.assertEqual(meta["github"], "github.com/johndoe-code")
        self.assertGreater(meta["word_count"], 10)


class TestParsers(unittest.TestCase):
    """Tests for PDF and DOCX parsers including empty, corrupted, and normal files."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_valid_pdf(self):
        pdf_path = os.path.join(self.temp_dir.name, "valid.pdf")
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(50, 50, 500, 700), "Senior Python Engineer with 5 years experience in PyTorch and AWS.")
        doc.save(pdf_path)
        doc.close()

        res = parse_resume(pdf_path, filename="valid.pdf")
        self.assertEqual(res["status"], "success")
        self.assertIn("Senior Python Engineer", res["clean_text"])
        self.assertFalse(res["is_scanned"])

    def test_parse_empty_pdf(self):
        empty_pdf = os.path.join(self.temp_dir.name, "empty.pdf")
        with open(empty_pdf, "wb") as f:
            f.write(b"")

        res = parse_resume(empty_pdf, filename="empty.pdf")
        self.assertNotEqual(res["status"], "success")
        self.assertIn("empty", res["error_message"].lower())

    def test_parse_scanned_pdf_detects_no_selectable_text(self):
        # A PDF with a blank page (0 text characters) mimics a scanned/image-only page without text
        scanned_pdf = os.path.join(self.temp_dir.name, "scanned.pdf")
        doc = pymupdf.open()
        doc.new_page()  # empty canvas
        doc.save(scanned_pdf)
        doc.close()

        res = parse_resume(scanned_pdf, filename="scanned.pdf")
        self.assertNotEqual(res["status"], "success")
        self.assertTrue(res["is_scanned"])

    def test_parse_valid_docx(self):
        docx_path = os.path.join(self.temp_dir.name, "valid.docx")
        doc = docx.Document()
        doc.add_paragraph("Full-Stack Developer skilled in React, TypeScript, and FastAPI.")
        doc.save(docx_path)

        res = parse_resume(docx_path, filename="valid.docx")
        self.assertEqual(res["status"], "success")
        self.assertIn("Full-Stack Developer", res["clean_text"])

    def test_parse_empty_docx(self):
        empty_docx = os.path.join(self.temp_dir.name, "empty.docx")
        with open(empty_docx, "wb") as f:
            f.write(b"")

        res = parse_resume(empty_docx, filename="empty.docx")
        self.assertNotEqual(res["status"], "success")
        self.assertIn("empty", res["error_message"].lower())

    def test_parse_corrupted_docx(self):
        corrupt_docx = os.path.join(self.temp_dir.name, "corrupt.docx")
        with open(corrupt_docx, "wb") as f:
            f.write(b"This is not a valid zip or docx file content.")

        res = parse_resume(corrupt_docx, filename="corrupt.docx")
        self.assertNotEqual(res["status"], "success")


class TestSkillExtractionAndDisambiguation(unittest.TestCase):
    """Tests taxonomy matching and ensures no false positives for single letters or common English verbs."""

    def test_multi_word_skill_extraction(self):
        text = "Experienced in machine learning, deep learning, retrieval augmented generation, and natural language processing."
        extracted = extract_skills_from_text(text)
        skills = extracted["display_skills"]
        self.assertIn("Machine Learning", skills)
        self.assertIn("Deep Learning", skills)
        self.assertIn("Retrieval Augmented Generation", skills)
        self.assertIn("Natural Language Processing", skills)

    def test_symbols_c_plus_plus_and_c_sharp_and_dot_net(self):
        text = "Built high-performance microservices using C++, C#, and .NET Core."
        extracted = extract_skills_from_text(text)
        skills = extracted["display_skills"]
        self.assertIn("C++", skills)
        self.assertIn("C#", skills)
        self.assertIn(".NET", skills)

    def test_false_positive_disambiguation(self):
        # A common English sentence should NOT match C, R, or Go
        sentence = "John R. Smith went to go to college and got grade C in history."
        extracted = extract_skills_from_text(sentence)
        self.assertEqual(extracted["count"], 0)
        self.assertNotIn("C", extracted["display_skills"])
        self.assertNotIn("R", extracted["display_skills"])
        self.assertNotIn("Go", extracted["display_skills"])

    def test_legitimate_c_r_go_programming_in_skills_list(self):
        text = "Technical Skills: C, C++, Python, R, Golang, SQL"
        extracted = extract_skills_from_text(text)
        skills = extracted["display_skills"]
        self.assertIn("C", skills)
        self.assertIn("C++", skills)
        self.assertIn("Python", skills)
        self.assertIn("R", skills)
        self.assertIn("Golang", skills)
        self.assertIn("SQL", skills)

    def test_skill_gap_analysis(self):
        jd = "Required: Python, PyTorch, Docker, Kubernetes, AWS, SQL."
        resume = "Experienced in Python, PyTorch, Docker, Git, MongoDB."

        gap = analyze_skill_gap(resume, jd)
        self.assertIn("Python", gap["matched_skills"])
        self.assertIn("PyTorch", gap["matched_skills"])
        self.assertIn("Docker", gap["matched_skills"])
        self.assertIn("AWS", gap["missing_skills"])
        self.assertIn("Kubernetes", gap["missing_skills"])
        self.assertIn("MongoDB", gap["additional_skills"])
        self.assertGreater(gap["skill_match_percentage"], 0.0)
        self.assertLess(gap["skill_match_percentage"], 100.0)


class TestEmbeddingsAndRanking(unittest.TestCase):
    """Tests embedding generation, batch cosine similarity, ranking, and explainability."""

    @classmethod
    def setUpClass(cls):
        cls.model, cls.backend = load_sentence_transformer_model(DEFAULT_MODEL_NAME)

    def test_model_loaded(self):
        self.assertIsNotNone(self.model)

    def test_semantic_similarity_relevant_vs_irrelevant(self):
        jd = "Senior Python developer with experience in machine learning, PyTorch, and deep learning algorithms."
        relevant_resume = "Machine learning engineer with 4 years designing neural networks in Python, PyTorch, and transformers."
        irrelevant_resume = "Executive chef specializing in Italian pizza dough, pasta sauces, kitchen management, and food safety."

        sim_rel, _ = compute_semantic_similarity(relevant_resume, jd, model=self.model)
        sim_irrel, _ = compute_semantic_similarity(irrelevant_resume, jd, model=self.model)

        self.assertGreater(sim_rel, 0.55)
        self.assertLess(sim_irrel, 0.35)
        self.assertGreater(sim_rel, sim_irrel)

    def test_batch_compute_similarity_with_empty_resume(self):
        jd = "Python engineer with cloud experience."
        resumes = [
            {"clean_text": "Python cloud developer with AWS experience."},
            {"clean_text": ""},  # empty
            {"clean_text": "Java backend engineer with Spring Boot."}
        ]
        sims = batch_compute_similarity(resumes, jd, model=self.model)
        self.assertEqual(len(sims), 3)
        self.assertGreater(sims[0], 0.4)
        self.assertEqual(sims[1], 0.0)  # Empty must strictly be 0.0
        self.assertGreater(sims[2], 0.0)

    def test_ranking_and_composite_score(self):
        jd = SAMPLE_JOB_DESCRIPTIONS["AI / Machine Learning Engineer"]
        resumes = [
            {
                "filename": "Candidate_AI.pdf",
                "clean_text": "Senior AI & Machine Learning Engineer with 5 years experience in Python, PyTorch, Deep Learning, Scikit-Learn, Transformers, Hugging Face, Docker, FastAPI, Kubernetes, and AWS.",
                "status": "success",
                "metadata": {"word_count": 250, "email": "ai@example.com"}
            },
            {
                "filename": "Candidate_Junior.pdf",
                "clean_text": "Junior developer with basic HTML, CSS, JavaScript, and Git.",
                "status": "success",
                "metadata": {"word_count": 180, "email": "jr@example.com"}
            },
            {
                "filename": "Corrupted_File.pdf",
                "clean_text": "",
                "status": "error",
                "error_message": "Corrupted file.",
                "metadata": {}
            }
        ]

        sims = batch_compute_similarity(resumes, jd, model=self.model)
        ranked, df_summary = rank_resumes(
            parsed_resumes=resumes,
            jd_text=jd,
            semantic_similarities=sims,
            semantic_weight=0.60,
            skill_weight=0.40,
            shortlist_threshold=50.0
        )

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["candidate_name"], "Candidate_AI.pdf")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertGreater(ranked[0]["composite_score"], ranked[1]["composite_score"])
        self.assertTrue(ranked[0]["is_shortlisted"])

        # Corrupted file must have rank '-' and 0.0 composite score
        failed_candidate = next(c for c in ranked if c["candidate_name"] == "Corrupted_File.pdf")
        self.assertEqual(failed_candidate["rank"], "-")
        self.assertEqual(failed_candidate["composite_score"], 0.0)
        self.assertFalse(failed_candidate["is_shortlisted"])

        # Check CSV generation
        csv_str = generate_csv_report(ranked)
        self.assertIn("Candidate_AI.pdf", csv_str)
        self.assertIn("Shortlisted", csv_str)
        self.assertIn("Failed / Unreadable File", csv_str)

    def test_explainable_ai_feedback_generation(self):
        skill_gap = {
            "matched_skills": ["Python", "PyTorch", "Docker"],
            "missing_skills": ["Kubernetes", "AWS"],
            "additional_skills": ["Redis"],
            "skill_match_percentage": 60.0
        }
        feedback = generate_explainable_feedback(
            candidate_name="Alex",
            composite_score=72.0,
            semantic_score_pct=75.0,
            skill_gap=skill_gap,
            metadata={"word_count": 350},
            text="Developed deep learning systems improving accuracy by 25%."
        )

        self.assertIn("overall_fit", feedback)
        self.assertIn("strengths", feedback)
        self.assertIn("gap_warnings", feedback)
        self.assertIn("actionable_suggestions", feedback)
        self.assertGreater(len(feedback["strengths"]), 0)
        self.assertGreater(len(feedback["gap_warnings"]), 0)


class TestValidationAndSafety(unittest.TestCase):
    """Tests input validation and safe handling of edge cases."""

    def test_validate_job_description_empty_and_short(self):
        val_empty, msg_empty = validate_job_description("")
        self.assertFalse(val_empty)
        self.assertIn("empty", msg_empty.lower())

        val_short, msg_short = validate_job_description("Software Engineer needed for our startup.")
        self.assertFalse(val_short)
        self.assertIn("brief", msg_short.lower())

        val_good, _ = validate_job_description(" " + "word " * 25)
        self.assertTrue(val_good)

    def test_validate_uploaded_files(self):
        class DummyFile:
            def __init__(self, name):
                self.name = name

        ok, errs = validate_uploaded_files([DummyFile("resume.pdf"), DummyFile("profile.docx")])
        self.assertTrue(ok)
        self.assertEqual(len(errs), 0)

        bad, bad_errs = validate_uploaded_files([DummyFile("resume.exe"), DummyFile("image.png")])
        self.assertFalse(bad)
        self.assertEqual(len(bad_errs), 2)


class TestCSVReportAndSafety(unittest.TestCase):
    """Tests for CSV report generation, formula injection sanitization, and filename safety."""

    def test_csv_formula_injection_sanitization(self):
        """Cells starting with =, +, -, @ must be prefixed with ' to prevent spreadsheet formula injection."""
        malicious_candidates = [
            {
                "rank": "=1+2",
                "candidate_name": "@evil_macro",
                "status": "+admin",
                "composite_score": 90.0,
                "semantic_score_pct": 85.0,
                "skill_match_pct": 95.0,
                "matched_skills": ["-Python", "=SQL"],
                "missing_skills": ["@AWS"],
                "additional_skills": [],
                "is_shortlisted": True,
                "metadata": {"email": "=cmd|' /C calc'!A0", "word_count": 300},
                "explanation": {
                    "score_breakdown": {"formula": "=(10*9)"},
                    "actionable_suggestions": ["+Add metrics"],
                    "review_needed_requirements": ["@Review this"]
                }
            }
        ]
        csv_output = generate_csv_report(malicious_candidates)
        # Check that dangerous operators are escaped with single quote
        self.assertIn("'=1+2", csv_output)
        self.assertIn("'@evil_macro", csv_output)
        self.assertIn("'+admin", csv_output)

    def test_sanitize_filename(self):
        """Path traversal characters and risky characters must be replaced."""
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("John Doe <Resume>.pdf"), "John_Doe__Resume_.pdf")
        self.assertEqual(sanitize_filename(""), "document")

    def test_csv_headers_and_structure(self):
        """Verifies that all standard export columns are generated properly."""
        sample = [
            {
                "rank": 1,
                "candidate_name": "Normal_Candidate.pdf",
                "status": "Processed",
                "composite_score": 82.5,
                "semantic_score_pct": 80.0,
                "skill_match_pct": 85.0,
                "matched_skills": ["Python", "Docker"],
                "missing_skills": ["AWS"],
                "additional_skills": ["FastAPI"],
                "is_shortlisted": True,
                "metadata": {"email": "test@example.com", "word_count": 250},
                "explanation": {
                    "score_breakdown": {"formula": "80.0% * 0.6 + 85.0% * 0.4 = 82.5%"},
                    "actionable_suggestions": ["Add metrics"],
                    "review_needed_requirements": ["AWS"]
                }
            }
        ]
        csv_output = generate_csv_report(sample)
        headers = [
            "Rank", "Candidate / Filename", "Status", "Overall Match (%)",
            "Semantic Sim (%)", "Skill Match (%)", "Matched Skills Count",
            "Missing Skills Count", "Decision Recommendation", "Score Calculation Formula"
        ]
        for h in headers:
            self.assertIn(h, csv_output)
        self.assertIn("Normal_Candidate.pdf", csv_output)
        self.assertIn("Shortlisted", csv_output)


if __name__ == "__main__":
    unittest.main()
