"""
Unit & Integration Tests for Admin & User Login Separation, RBAC, and SQLite Persistence.
Tests:
- Automatic seeding and provisioning of initial administrator account
- Bcrypt password hashing and verification
- Strict Role-Based Access Control (RBAC): user cannot login as admin, admin cannot login as user
- Prevention of privilege escalation during public registration
- User management lifecycle (activate, deactivate, delete)
- Job management CRUD
- Resume and screening record relational persistence
"""

import unittest
import os
import sqlite3
from src.database import (
    init_db,
    db_get_user_by_email,
    db_get_user_by_id,
    db_create_user,
    db_set_user_status,
    db_delete_user,
    db_add_job,
    db_update_job,
    db_delete_job,
    db_get_all_jobs,
    db_add_resume_record,
    db_get_all_resumes,
    db_delete_resume_record,
    db_add_screening_record,
    db_get_screening_metrics,
    db_create_password_reset_token,
    db_verify_and_consume_reset_token,
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


class TestAdminAndRBAC(unittest.TestCase):
    """Test suite for Admin & User Login portals, RBAC, and SQLite persistence."""

    @classmethod
    def setUpClass(cls):
        """Ensure database schema is initialized and seeded before running tests."""
        init_db()

    def setUp(self):
        """Clean up test users before each test."""
        for email in ["test_rbac_user@example.com", "hacker@test.com", "lifecycle_user@example.com"]:
            u = db_get_user_by_email(email)
            if u:
                db_delete_user(u["id"])

    def tearDown(self):
        """Clean up test users after each test."""
        for email in ["test_rbac_user@example.com", "hacker@test.com", "lifecycle_user@example.com"]:
            u = db_get_user_by_email(email)
            if u:
                db_delete_user(u["id"])

    def test_admin_provisioning_and_login(self):
        """Verifies initial admin account exists in SQLite and logs in with bcrypt verification."""
        admin_row = db_get_user_by_email(DEFAULT_ADMIN_EMAIL)
        self.assertIsNotNone(admin_row, "Default admin account should be seeded in SQLite.")
        self.assertEqual(admin_row["role"], "admin")
        self.assertEqual(admin_row["status"], "active")

        # Verify password hash is bcrypt
        self.assertTrue(admin_row["password_hash"].startswith(("$2a$", "$2b$", "$2y$")), "Admin password must be bcrypt-hashed.")
        self.assertTrue(verify_password_bcrypt(DEFAULT_ADMIN_PASSWORD, admin_row["password_hash"]))

        # Authenticate via auth module with required_role='admin'
        succ, admin_user, msg = authenticate_user(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, required_role="admin")
        self.assertTrue(succ, f"Admin login failed: {msg}")
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user["role"], "admin")
        self.assertTrue(is_admin(admin_user))
        self.assertFalse(is_user(admin_user))

    def test_strict_role_separation(self):
        """Verifies regular users cannot access admin portal and admins cannot access user portal."""
        # 1. Normal user attempting admin login
        succ_user_as_admin, _, msg_user_as_admin = authenticate_user(
            "recruiter@resumerank.ai", "Recruiter@2026", required_role="admin"
        )
        self.assertFalse(succ_user_as_admin)
        self.assertIn("Access Denied", msg_user_as_admin)

        # 2. Administrator attempting user login
        succ_admin_as_user, _, msg_admin_as_user = authenticate_user(
            DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, required_role="user"
        )
        self.assertFalse(succ_admin_as_user)
        self.assertIn("Administrator credentials detected", msg_admin_as_user)

    def test_prevention_of_privilege_escalation(self):
        """Verifies public registration cannot create an administrator account."""
        succ, hacker, msg = register_user(
            "hacker@test.com", "HackerPass123!", "Malicious Actor", role="admin"
        )
        self.assertFalse(succ)
        self.assertIsNone(hacker)
        self.assertIn("administrator", msg.lower())

        # Ensure account was NOT created
        db_user = db_get_user_by_email("hacker@test.com")
        self.assertIsNone(db_user)

    def test_user_registration_and_rbac(self):
        """Verifies normal registration assigns user permissions."""
        email = "test_rbac_user@example.com"
        pwd = "SafeUserPass123!"
        succ, user, msg = register_user(email, pwd, "Test Candidate", role="user")
        self.assertTrue(succ, f"Registration failed: {msg}")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "user")
        self.assertTrue(is_user(user))
        self.assertFalse(is_admin(user))

        # Test login in user portal
        login_succ, login_user, _ = authenticate_user(email, pwd, required_role="user")
        self.assertTrue(login_succ)
        self.assertEqual(login_user["email"], email)

    def test_user_management_lifecycle(self):
        """Verifies admin user management: status toggle (activate/deactivate) and deletion."""
        email = "lifecycle_user@example.com"
        pwd = "LifeCycle2026!"
        succ, user, _ = register_user(email, pwd, "Lifecycle User", role="user")
        self.assertTrue(succ)
        user_id = user["id"]

        # Deactivate user
        ok, msg = db_set_user_status(user_id, "inactive")
        self.assertTrue(ok)

        # Login should now fail because account is inactive
        login_succ, _, login_msg = authenticate_user(email, pwd, required_role="user")
        self.assertFalse(login_succ)
        self.assertIn("inactive", login_msg.lower())

        # Reactivate user
        ok, _ = db_set_user_status(user_id, "active")
        self.assertTrue(ok)
        login_succ2, _, _ = authenticate_user(email, pwd, required_role="user")
        self.assertTrue(login_succ2)

        # Delete user
        del_ok, _ = db_delete_user(user_id)
        self.assertTrue(del_ok)
        self.assertIsNone(db_get_user_by_id(user_id))

    def test_job_management_crud(self):
        """Verifies creating, updating, retrieving, and deleting jobs in SQLite."""
        ok, msg, job_id = db_add_job(
            title="Senior MLOps Architect",
            description="Lead production AI inference pipelines and Kubernetes clusters.",
            department="Machine Learning Infrastructure",
            experience_level="Lead / Principal",
            created_by="admin"
        )
        self.assertTrue(ok, f"Failed to add job: {msg}")
        self.assertIsNotNone(job_id)

        # Verify job is in list
        jobs = db_get_all_jobs()
        matched = [j for j in jobs if j["id"] == job_id]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["title"], "Senior MLOps Architect")

        # Update job
        upd_ok, _ = db_update_job(
            job_id=job_id,
            title="Principal MLOps Architect",
            description="Architect hyper-scale AI platforms.",
            department="Infrastructure Engineering",
            experience_level="Principal"
        )
        self.assertTrue(upd_ok)

        # Delete job
        del_ok, _ = db_delete_job(job_id)
        self.assertTrue(del_ok)

    def test_resume_and_screening_persistence(self):
        """Verifies storing resume metadata and screening audit logs in SQLite."""
        admin = db_get_user_by_email(DEFAULT_ADMIN_EMAIL)
        self.assertIsNotNone(admin)
        admin_id = admin["id"]

        res_id = db_add_resume_record(
            user_id=admin_id,
            filename="alex_rivera_cv.pdf",
            file_type="pdf",
            word_count=350,
            extracted_email="alex.rivera@example.com",
            candidate_name="Alex Rivera",
            skills_detected=["Python", "PyTorch", "Docker"],
            status="parsed"
        )
        self.assertGreater(res_id, 0)

        # Verify in all resumes
        all_res = db_get_all_resumes()
        matching = [r for r in all_res if r["id"] == res_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["candidate_name"], "Alex Rivera")

        # Add screening record
        scr_id = db_add_screening_record(
            user_id=admin_id,
            job_title="AI / Machine Learning Engineer",
            candidate_name="Alex Rivera",
            filename="alex_rivera_cv.pdf",
            composite_score=87.5,
            semantic_score=85.0,
            skill_score=90.0,
            decision="SHORTLISTED"
        )
        self.assertGreater(scr_id, 0)

        # Check screening metrics
        metrics = db_get_screening_metrics()
        self.assertGreaterEqual(metrics["total_screenings"], 1)

        # Clean up resume
        self.assertTrue(db_delete_resume_record(res_id))

    def test_password_reset_token_flow(self):
        """Verifies single-use password reset token creation and consumption in SQLite."""
        test_email = "reset_test@airesume.com"
        token = db_create_password_reset_token(test_email, expiry_seconds=300)
        self.assertTrue(token.startswith("rst_"))

        # Verify and consume
        consumed_email = db_verify_and_consume_reset_token(token)
        self.assertEqual(consumed_email, test_email)

        # Single-use: consuming again must return None
        consumed_again = db_verify_and_consume_reset_token(token)
        self.assertIsNone(consumed_again)


    def test_login_rate_limiting(self):
        """Verifies brute-force rate limiting locks out accounts after excessive failures."""
        reset_all_rate_limits()
        bad_email = "ratelimit_target@example.com"
        
        # 5 consecutive failed attempts
        for i in range(5):
            succ, _, msg = authenticate_user(bad_email, "WrongPass123!")
            self.assertFalse(succ)
        
        # 6th attempt should be blocked by rate limiter
        succ_6, _, msg_6 = authenticate_user(bad_email, "WrongPass123!")
        self.assertFalse(succ_6)
        self.assertIn("temporarily locked", msg_6.lower())

        # Reset rate limits
        reset_all_rate_limits()
        succ_after_reset, _, msg_after_reset = authenticate_user(bad_email, "WrongPass123!")
        self.assertFalse(succ_after_reset)
        self.assertNotIn("temporarily locked", msg_after_reset.lower())


if __name__ == "__main__":
    unittest.main()
