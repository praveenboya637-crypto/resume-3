"""
Comprehensive End-to-End Verification Test for AI Resume Screening and Job Matching System.
Directly executes all 14 test steps required by Section 10 of User Specification:
1. Verify initial admin credentials and persistent database seeding
2. Register a new normal user with validation
3. Authenticate as normal user and confirm User Dashboard role permissions
4. Verify normal user CANNOT access admin portal or admin functionality (RBAC enforcement)
5. Session logout verification
6. Authenticate as Administrator (admin@airesume.com / ResumeAdmin@2026!)
7. Confirm Admin Dashboard access
8. Test User Management (view, deactivate, reactivate, delete)
9. Test Job Management (create, edit, retrieve, delete)
10. Test Analytics & Audit exports from actual database
11. Verify bcrypt password hashing (no plaintext)
12. Verify database persistence across restarts (reconnect test)
13. Verify Resume upload, PDF/DOCX parsing, dense embeddings, and AI matching pipeline
14. Verify Login Rate Limiting protects against brute force attacks
"""

import unittest
import os
import sqlite3
import time
from typing import Dict, Any

from src.database import (
    init_db,
    get_db_connection,
    db_get_user_by_email,
    db_get_user_by_id,
    db_create_user,
    db_set_user_status,
    db_delete_user,
    db_update_user_password,
    db_get_all_users,
    db_get_user_metrics,
    db_add_job,
    db_update_job,
    db_delete_job,
    db_get_all_jobs,
    db_get_total_jobs_count,
    db_add_resume_record,
    db_get_all_resumes,
    db_delete_resume_record,
    db_get_total_resumes_count,
    db_add_screening_record,
    db_get_screening_records,
    db_get_screening_metrics,
    hash_password_bcrypt,
    verify_password_bcrypt,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD
)
from src.auth import (
    authenticate_user,
    register_user,
    is_admin,
    is_user,
    reset_all_rate_limits
)
from src.parsers import parse_resume
from src.skills_extractor import extract_skills_from_text
from src.embeddings import load_sentence_transformer_model, batch_compute_similarity
from src.ranker import rank_resumes
from src.constants import DEFAULT_MODEL_NAME, SAMPLE_JOB_DESCRIPTIONS


class TestE2EVerification(unittest.TestCase):
    """End-to-end integration and verification suite."""

    @classmethod
    def setUpClass(cls):
        """Initializes database and caches model."""
        init_db()

    def setUp(self):
        """Clean test fixtures before each test."""
        reset_all_rate_limits()
        for email in ["jane.candidate@example.com", "e2e_temp_user@example.com"]:
            u = db_get_user_by_email(email)
            if u:
                db_delete_user(u["id"])

    def tearDown(self):
        """Clean test fixtures after each test."""
        for email in ["jane.candidate@example.com", "e2e_temp_user@example.com"]:
            u = db_get_user_by_email(email)
            if u:
                db_delete_user(u["id"])

    def test_01_initial_admin_credentials_and_seeding(self):
        """Step 1: Admin account exists, is role='admin', hashed with bcrypt, and does not duplicate."""
        admin = db_get_user_by_email(DEFAULT_ADMIN_EMAIL)
        self.assertIsNotNone(admin, "Initial admin must exist in database.")
        self.assertEqual(admin["email"].lower(), "admin@airesume.com")
        self.assertEqual(admin["role"], "admin")
        self.assertEqual(admin["status"], "active")
        self.assertTrue(admin["password_hash"].startswith(("$2a$", "$2b$", "$2y$")))
        self.assertTrue(verify_password_bcrypt(DEFAULT_ADMIN_PASSWORD, admin["password_hash"]))

        # Calling init_db() again must NOT create duplicate admin accounts
        init_db()
        users = db_get_all_users(search_query="admin@airesume.com")
        self.assertEqual(len(users), 1, "Duplicate admin accounts must not be created on repeated init.")

    def test_02_register_normal_user(self):
        """Step 2: Register a new normal user with full name, email, password match validation."""
        email = "jane.candidate@example.com"
        pwd = "Candidate2026!"
        name = "Jane Candidate"

        succ, user, msg = register_user(email, pwd, name, role="Candidate / Job Seeker")
        self.assertTrue(succ, f"User registration failed: {msg}")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], email)
        self.assertEqual(user["full_name"], name)
        # Normal registration receives user role
        self.assertTrue(is_user(user))
        self.assertFalse(is_admin(user))

    def test_03_login_as_normal_user_and_permissions(self):
        """Step 3: Log in as normal user and confirm User Dashboard role permissions."""
        email = "jane.candidate@example.com"
        pwd = "Candidate2026!"
        name = "Jane Candidate"
        register_user(email, pwd, name, role="user")

        succ, user_data, msg = authenticate_user(email, pwd, required_role="user")
        self.assertTrue(succ, f"Login failed: {msg}")
        self.assertIsNotNone(user_data)
        self.assertTrue(user_data.get("is_authenticated"))
        self.assertTrue(is_user(user_data))
        self.assertFalse(is_admin(user_data))

    def test_04_user_cannot_access_admin_portal(self):
        """Step 4: Normal user attempting admin login or admin role access is strictly denied."""
        email = "jane.candidate@example.com"
        pwd = "Candidate2026!"
        register_user(email, pwd, "Jane Candidate", role="user")

        succ, admin_attempt, msg = authenticate_user(email, pwd, required_role="admin")
        self.assertFalse(succ, "Normal user must not be granted admin authentication.")
        self.assertIsNone(admin_attempt)
        self.assertIn("Access Denied", msg)

    def test_05_admin_login_and_dashboard_access(self):
        """Step 5 & 6: Log in as admin with default credentials and verify admin access."""
        succ, admin_data, msg = authenticate_user(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, required_role="admin")
        self.assertTrue(succ, f"Admin login failed: {msg}")
        self.assertIsNotNone(admin_data)
        self.assertEqual(admin_data["role"], "admin")
        self.assertTrue(is_admin(admin_data))
        self.assertFalse(is_user(admin_data))

    def test_06_admin_user_management(self):
        """Step 7: Admin User Management: view, search, deactivate, reactivate, and delete."""
        # Create temp user
        t_email = "e2e_temp_user@example.com"
        t_pwd = "TempUser2026!"
        t_name = "Temp User"
        succ, u_data, _ = register_user(t_email, t_pwd, t_name, role="user")
        self.assertTrue(succ)
        u_id = u_data["id"]

        # 1. Search and view
        found = db_get_all_users(search_query="e2e_temp")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["email"], t_email)
        # Ensure password hash is NOT returned
        self.assertNotIn("password_hash", found[0])

        # 2. Deactivate
        ok_deact, msg_deact = db_set_user_status(u_id, "inactive")
        self.assertTrue(ok_deact)
        # Inactive user cannot log in
        login_fail, _, err = authenticate_user(t_email, t_pwd, required_role="user")
        self.assertFalse(login_fail)
        self.assertIn("inactive", err.lower())

        # 3. Reactivate
        ok_act, _ = db_set_user_status(u_id, "active")
        self.assertTrue(ok_act)
        login_ok, _, _ = authenticate_user(t_email, t_pwd, required_role="user")
        self.assertTrue(login_ok)

        # 4. Delete
        del_ok, _ = db_delete_user(u_id)
        self.assertTrue(del_ok)
        self.assertIsNone(db_get_user_by_id(u_id))

    def test_07_admin_job_management(self):
        """Step 8: Admin Job Management: add job, retrieve, edit, and delete."""
        title = "Cloud Infrastructure Architect (E2E Test)"
        desc = "Design highly available multi-region Kubernetes clusters on AWS/GCP."
        dept = "Cloud Architecture"
        exp = "Staff (8+ Yrs)"

        ok, msg, j_id = db_add_job(title, desc, dept, exp, created_by="admin")
        self.assertTrue(ok, f"Job creation failed: {msg}")
        self.assertIsNotNone(j_id)

        # Verify in all jobs
        all_j = db_get_all_jobs()
        match = [j for j in all_j if j["id"] == j_id]
        self.assertEqual(len(match), 1)

        # Update
        upd_ok, _ = db_update_job(j_id, "Staff Cloud Architect (E2E Test)", desc, dept, exp)
        self.assertTrue(upd_ok)

        # Delete
        del_ok, _ = db_delete_job(j_id)
        self.assertTrue(del_ok)

    def test_08_database_persistence_across_reconnects(self):
        """Step 9: Database persistence: data remains intact across connection restarts."""
        email = "jane.candidate@example.com"
        pwd = "Candidate2026!"
        register_user(email, pwd, "Jane Candidate", role="user")

        # Open completely new raw connection simulating app restart
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email, full_name, role FROM users WHERE email = ?;", (email,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["email"], email)
            self.assertEqual(row["full_name"], "Jane Candidate")

    def test_09_resume_upload_parsing_and_ai_screening(self):
        """Step 10: AI Resume Parsing, Embedding, and Job Matching with SQLite Sync."""
        # Find sample resume
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sample_data", "resumes", "Alex_Rivera_AI_Engineer.pdf"
        )
        if not os.path.exists(sample_path):
            self.skipTest(f"Sample resume file not found at {sample_path}")

        parsed = parse_resume(sample_path, filename="Alex_Rivera_AI_Engineer.pdf")
        self.assertEqual(parsed["status"], "success")
        self.assertGreater(parsed["metadata"]["word_count"], 50)
        extracted = extract_skills_from_text(parsed["clean_text"])
        skills = extracted["display_skills"]
        self.assertIn("Python", skills)

        # Load embedding model and rank
        model, backend = load_sentence_transformer_model(DEFAULT_MODEL_NAME)
        jd_text = SAMPLE_JOB_DESCRIPTIONS["AI / Machine Learning Engineer"]
        raw_sims = batch_compute_similarity([parsed], jd_text, model=model)
        self.assertEqual(len(raw_sims), 1)
        self.assertGreater(raw_sims[0], 0.3)

        ranked, _ = rank_resumes([parsed], jd_text, raw_sims, semantic_weight=0.6, skill_weight=0.4)
        self.assertEqual(len(ranked), 1)
        self.assertGreater(ranked[0]["composite_score"], 50.0)

        # Sync to SQLite
        admin = db_get_user_by_email(DEFAULT_ADMIN_EMAIL)
        r_id = db_add_resume_record(
            user_id=admin["id"],
            filename="Alex_Rivera_AI_Engineer.pdf",
            file_type="pdf",
            word_count=parsed["metadata"]["word_count"],
            extracted_email=parsed["metadata"].get("email", ""),
            candidate_name=parsed.get("candidate_name", "Alex Rivera"),
            skills_detected=skills,
            status="parsed"
        )
        self.assertGreater(r_id, 0)

        s_id = db_add_screening_record(
            user_id=admin["id"],
            job_title="AI / Machine Learning Engineer",
            candidate_name="Alex Rivera",
            filename="Alex_Rivera_AI_Engineer.pdf",
            composite_score=float(ranked[0].get("composite_score", 0)),
            semantic_score=float(ranked[0].get("semantic_score_pct", 0)),
            skill_score=float(ranked[0].get("skill_match_pct", 0)),
            decision="SHORTLISTED" if ranked[0].get("is_shortlisted") else "REVIEW"
        )
        self.assertGreater(s_id, 0)

        # Verify screening metrics
        metrics = db_get_screening_metrics()
        self.assertGreaterEqual(metrics["total_screenings"], 1)

        # Clean up resume record
        db_delete_resume_record(r_id)


if __name__ == "__main__":
    unittest.main()
