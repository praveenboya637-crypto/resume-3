"""
Unit and integration tests for Resume Builder, PDF Generator, and Resume Quality Engine.
Tests:
- PDF generation across all 3 templates (Modern, Minimal ATS, Technical)
- Fresher profile vs Experienced profile
- Multi-page overflow and pagination with NumberedCanvas
- PyMuPDF text extraction compatibility
- Resume Quality & ATS Completeness scoring and metrics detection
- HTML preview rendering and XSS escaping
- Integration with TalentIQ screening parser and skills extractor
"""

import unittest
import pymupdf
from src.pdf_generator import generate_resume_pdf, get_download_filename
from src.resume_quality import evaluate_resume_quality, _detect_metrics, _has_action_verb
from src.resume_templates import get_resume_preview_html
from src.parsers import extract_text_from_pdf
from src.skills_extractor import extract_skills_from_text, analyze_skill_gap
from src.resume_builder_view import SAMPLE_FRESHER_DATA, extract_candidate_name_from_filename

# Isolated test fixture for experienced candidate tests
TEST_EXPERIENCED_DATA = {
    "full_name": "Jordan Blake",
    "headline": "Lead AI / Systems Architect",
    "email": "jordan.blake@example.com",
    "phone": "+1 (555) 438-9201",
    "location": "San Francisco, CA & Remote",
    "linkedin": "https://linkedin.com/in/jordanblake-ai",
    "github": "https://github.com/jordanblake-ml",
    "portfolio": "https://jordanblake.dev",
    "summary": "Accomplished Machine Learning Engineer with 6+ years of expertise architecting high-performance distributed AI systems and cloud-native microservices. Spearheaded LLM fine-tuning pipelines and containerized RAG search that reduced latency by 45% and scaled to support 150k daily active requests.",
    "skills_languages": "Python, SQL, Go, C++, TypeScript, Bash",
    "skills_tech": "PyTorch, Deep Learning, NLP, Transformers, LLM, Generative AI, RAG, Scikit-Learn",
    "skills_tools": "Docker, Kubernetes, AWS, GCP, FastAPI, CI/CD, Redis, PostgreSQL, Git",
    "skills_soft": "System Architecture, Cross-Functional Team Leadership, Agile / Scrum, Technical Mentorship",
    "is_fresher": False,
    "experience": [
        {
            "company": "Apex Cloud Systems",
            "role": "Lead AI Infrastructure Engineer",
            "start_date": "2022",
            "end_date": "Present",
            "current": True,
            "description": "Architected distributed training and inference clusters across 32 NVIDIA H100 GPUs, accelerating fine-tuning cycles by 55%.\nEngineered containerized RAG retrieval pipelines using FastAPI, pgvector, and Redis, serving 120,000 queries daily with sub-40ms latency.\nSpearheaded CI/CD automation and Docker deployment pipelines, eliminating 95% of manual staging friction."
        }
    ],
    "projects": [
        {
            "title": "Enterprise Vector Search Gateway",
            "technologies": "Python, PyTorch, Transformers, FastAPI, Docker",
            "link": "https://github.com/jordanblake-ml/vector-search",
            "description": "Engineered an open-source enterprise retrieval-augmented generation engine with hybrid dense-sparse reranking.",
            "achievements": "Achieved 92% retrieval precision on technical documents; accumulated 850+ GitHub stars."
        }
    ],
    "education": [
        {
            "institution": "MIT",
            "degree": "Master of Science",
            "field": "Computer Science (Artificial Intelligence)",
            "start_year": "2017",
            "end_year": "2019",
            "cgpa": "3.91 / 4.0"
        }
    ],
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect – Professional",
            "issuer": "Amazon Web Services",
            "year": "2023",
            "details": "Active Credential"
        }
    ],
    "additional_sections": {
        "Relevant Coursework": "Distributed Systems, Deep Learning, Cloud Computing Architecture",
        "Languages": "English (Native)"
    }
}


class TestResumeBuilder(unittest.TestCase):

    def setUp(self):
        self.experienced_data = dict(TEST_EXPERIENCED_DATA)
        self.fresher_data = dict(SAMPLE_FRESHER_DATA)

    def test_pdf_generation_three_templates_experienced(self):
        """Tests that all 3 templates generate valid, non-empty PDFs for experienced candidates."""
        templates = [
            "Modern Professional",
            "Minimal ATS-Friendly",
            "Technical / Software Developer"
        ]
        for tmpl in templates:
            pdf_bytes = generate_resume_pdf(self.experienced_data, tmpl)
            self.assertIsInstance(pdf_bytes, bytes)
            self.assertGreater(len(pdf_bytes), 2000, f"PDF byte count too small for {tmpl}")

            # Verify PyMuPDF opens and extracts text
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            self.assertGreaterEqual(len(doc), 1)
            full_text = "".join(page.get_text() for page in doc)

            self.assertTrue("Jordan Blake" in full_text or "JORDAN BLAKE" in full_text, f"Candidate name missing in {tmpl}")
            self.assertIn("jordan.blake@example.com", full_text, f"Email missing in {tmpl}")
            self.assertIn("Apex Cloud Systems", full_text, f"Experience company missing in {tmpl}")
            self.assertIn("Enterprise Vector Search Gateway", full_text, f"Project missing in {tmpl}")
            self.assertIn("MIT", full_text, f"Education missing in {tmpl}")

    def test_pdf_generation_fresher(self):
        """Tests that fresher profiles without work experience render cleanly."""
        pdf_bytes = generate_resume_pdf(self.fresher_data, "Minimal ATS-Friendly")
        self.assertGreater(len(pdf_bytes), 1500)

        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "".join(page.get_text() for page in doc)

        self.assertTrue("Maya Patel" in full_text or "MAYA PATEL" in full_text)
        self.assertIn("maya.patel@example.com", full_text)
        self.assertIn("Smart Vision Edge Defect Detector", full_text)
        self.assertIn("Northeastern University", full_text)
        # Should not crash on empty experience
        self.assertNotIn("NeuralScale", full_text)

    def test_multi_page_pdf_flow(self):
        """Tests long resumes that flow across multiple pages with NumberedCanvas footers."""
        long_data = dict(self.experienced_data)
        long_data["summary"] = "Detailed career summary of scalable systems. " * 30
        long_data["experience"] = [
            {
                "company": f"Enterprise Scale Labs {i}",
                "role": f"Principal Systems Architect {i}",
                "start_date": f"201{i}",
                "end_date": f"202{i}",
                "description": "\n".join([
                    f"Spearheaded core microservices cluster #{j}, reducing latency by 45% and serving 10M requests daily."
                    for j in range(4)
                ])
            }
            for i in range(4)
        ]
        long_data["projects"] = [
            {
                "title": f"Distributed Cloud Infrastructure {i}",
                "technologies": "Go, Kubernetes, Redis, Docker, gRPC",
                "link": "https://github.com/jordanblake-ml/project",
                "description": "Engineered distributed state store with Byzantine fault tolerance." * 3,
                "achievements": f"Handled 50,000 req/sec with 99.999% uptime for {i} enterprise customers."
            }
            for i in range(4)
        ]

        pdf_bytes = generate_resume_pdf(long_data, "Modern Professional")
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

        self.assertGreaterEqual(len(doc), 2, "Expected multi-page PDF generation for lengthy content")
        # Check running footer on page 2
        p2_text = doc[1].get_text()
        self.assertIn("Page 2 of", p2_text)

    def test_download_filename_sanitization(self):
        """Tests filename sanitization for downloaded PDFs."""
        self.assertEqual(get_download_filename("Jordan Blake"), "Jordan_Blake_Resume.pdf")
        self.assertEqual(get_download_filename("John Doe, Ph.D. / Jr."), "John_Doe_Ph.D._Jr._Resume.pdf")
        self.assertEqual(get_download_filename(""), "TalentIQ_Candidate_Resume.pdf")
        self.assertEqual(get_download_filename(None), "TalentIQ_Candidate_Resume.pdf")

    def test_resume_quality_evaluator_strong(self):
        """Tests that a complete profile scores high on quality."""
        audit = evaluate_resume_quality(self.experienced_data, "AI / Machine Learning Engineer")
        self.assertGreaterEqual(audit["score"], 88.0)
        self.assertEqual(audit["rating"], "Outstanding")
        self.assertEqual(len(audit["critical_missing"]), 0)
        self.assertGreater(len(audit["strengths"]), 4)
        self.assertGreater(len(audit["metrics_found"]), 0)
        self.assertGreater(len(audit["action_verbs_found"]), 0)

        # Target role advice
        role_adv = audit["role_advice"]
        self.assertEqual(role_adv["target_role"], "AI / Machine Learning Engineer")
        self.assertGreater(len(role_adv["matching"]), 0)

    def test_resume_quality_evaluator_missing_fields(self):
        """Tests that missing required fields are correctly flagged."""
        empty_data = {
            "full_name": "",
            "headline": "",
            "email": "",
            "summary": "",
            "skills_tech": "",
            "skills_languages": "",
            "education": []
        }
        audit = evaluate_resume_quality(empty_data)
        self.assertLess(audit["score"], 40.0)
        self.assertEqual(audit["rating"], "Needs Improvement")
        self.assertTrue(any("Full Name" in item for item in audit["critical_missing"]))
        self.assertTrue(any("Email" in item for item in audit["critical_missing"]))
        self.assertTrue(any("Education" in item for item in audit["critical_missing"]))
        self.assertTrue(any("Skills" in item for item in audit["critical_missing"]))

    def test_detect_metrics_and_action_verbs(self):
        """Tests regex metric detector and action verb analyzer."""
        sample_bullet = "Reduced end-to-end inference latency by 45% and saved $65,000 annually across 120,000 queries."
        metrics = _detect_metrics(sample_bullet)
        self.assertIn("45%", metrics)
        self.assertTrue(any("65,000" in m or "$65,000" in m for m in metrics))
        self.assertTrue(any("120,000 queries" in m for m in metrics))

        self.assertTrue(_has_action_verb("Architected high-throughput RAG search"))
        self.assertTrue(_has_action_verb("Spearheaded containerization"))
        self.assertFalse(_has_action_verb("Responsible for maintaining servers"))

    def test_live_preview_html_rendering_and_escaping(self):
        """Tests live HTML rendering, CommonMark formatting safety, and XSS sanitization."""
        test_data = dict(self.experienced_data)
        test_data["headline"] = "Software Engineer <script>alert(1)</script> & Architect"
        test_data["github"] = "javascript:alert('xss')"

        for tmpl in ["Modern Professional", "Minimal ATS-Friendly", "Technical / Software Developer"]:
            html_content = get_resume_preview_html(test_data, tmpl)
            self.assertNotIn("<script>", html_content)
            self.assertIn("&lt;script&gt;", html_content)
            self.assertNotIn("javascript:", html_content)
            self.assertTrue("Jordan Blake" in html_content or "JORDAN BLAKE" in html_content)
            self.assertIn("jordan.blake@example.com", html_content)
            # Ensure no line is indented with 4+ spaces so CommonMark does not create <pre><code> code blocks
            self.assertFalse(any(line.startswith("    ") for line in html_content.splitlines()))

            # Verify that Markdown parser renders real HTML elements without raw tag escaping
            import markdown_it
            md = markdown_it.MarkdownIt()
            rendered = md.render(html_content)
            self.assertNotIn("<pre>", rendered, f"Indented code block detected in {tmpl}")
            self.assertNotIn("<code>", rendered, f"Code block detected in {tmpl}")
            self.assertNotIn("&lt;div", rendered, f"Escaped div tags detected in {tmpl}")

    def test_empty_state_detection(self):
        """Tests that blank/cleared resume dictionary correctly evaluates has_content as False."""
        empty_data = {
            "full_name": "",
            "headline": "",
            "email": "",
            "phone": "",
            "location": "",
            "summary": "",
            "skills_tech": "",
            "skills_languages": "",
            "experience": [],
            "projects": [],
            "education": []
        }
        has_content = bool(
            (empty_data.get("full_name") and empty_data.get("full_name").strip()) or
            (empty_data.get("summary") and empty_data.get("summary").strip()) or
            any((e.get("company") and e.get("company").strip()) or (e.get("role") and e.get("role").strip()) for e in empty_data.get("experience", [])) or
            any((p.get("title") and p.get("title").strip()) for p in empty_data.get("projects", [])) or
            any((ed.get("institution") and ed.get("institution").strip()) or (ed.get("degree") and ed.get("degree").strip()) for ed in empty_data.get("education", [])) or
            (empty_data.get("skills_tech") and empty_data.get("skills_tech").strip()) or
            (empty_data.get("skills_languages") and empty_data.get("skills_languages").strip())
        )
        self.assertFalse(has_content)

    def test_extract_candidate_name_from_filename(self):
        """Tests safe sanitization and extraction of candidate names from uploaded filenames."""
        self.assertEqual(extract_candidate_name_from_filename("Alex_Rivera_AI_Engineer.pdf"), "Alex Rivera Ai Engineer")
        self.assertEqual(extract_candidate_name_from_filename("John_Doe_Resume.pdf"), "John Doe")
        self.assertEqual(extract_candidate_name_from_filename("Resume_Jane_Smith.docx"), "Jane Smith")
        self.assertEqual(extract_candidate_name_from_filename("CV_David_Miller.pdf"), "David Miller")
        self.assertEqual(extract_candidate_name_from_filename("sam-taylor-cv.pdf"), "Sam Taylor")
        self.assertEqual(extract_candidate_name_from_filename("C:/path/to/Priya_Sharma.pdf"), "Priya Sharma")
        self.assertEqual(extract_candidate_name_from_filename("Resume.pdf"), "Candidate")
        self.assertEqual(extract_candidate_name_from_filename("CV.docx"), "Candidate")
        self.assertEqual(extract_candidate_name_from_filename(""), "Candidate")
        self.assertEqual(extract_candidate_name_from_filename(None), "Candidate")
        self.assertEqual(extract_candidate_name_from_filename("McVey_Robert.pdf"), "Mcvey Robert")

    def test_screening_engine_parser_compatibility(self):
        """Tests that a generated PDF can be parsed by extract_text_from_pdf and skills extracted."""
        pdf_bytes = generate_resume_pdf(self.experienced_data, "Modern Professional")

        # PyMuPDF extraction
        extracted_text, pages, err, is_scanned = extract_text_from_pdf(pdf_bytes)
        self.assertIsNone(err)
        self.assertFalse(is_scanned)
        self.assertGreater(len(extracted_text), 200)

        # Skills extraction
        extracted_skills = extract_skills_from_text(extracted_text)
        detected = extracted_skills.get("display_skills", []) or extracted_skills.get("all_skills", [])
        self.assertTrue(any(s.lower() == "python" for s in detected))
        self.assertTrue(any(s.lower() == "pytorch" for s in detected))
        self.assertTrue(any(s.lower() == "docker" for s in detected))

        # Skill gap analysis against a JD
        sample_jd = "Looking for Senior AI Engineer with Python, PyTorch, Docker, Kubernetes, and AWS."
        gap = analyze_skill_gap(extracted_text, sample_jd)
        self.assertGreater(gap.get("skill_match_percentage", 0), 60.0)
        self.assertIn("Python", gap.get("matched_skills", []))
        self.assertIn("PyTorch", gap.get("matched_skills", []))


if __name__ == "__main__":
    unittest.main()
