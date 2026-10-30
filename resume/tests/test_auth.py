"""
Unit Tests for Authentication, Password Hashing, Validation, and Sandbox Role Controls.
"""

import unittest
from src.auth import (
    validate_email,
    validate_password_strength,
    authenticate_user,
    register_user,
    initiate_password_reset,
    complete_password_reset,
    get_auth_mode_info,
    _hash_password,
    _verify_password
)
from src.database import db_get_user_by_email, db_delete_user


class TestAuthModule(unittest.TestCase):
    """Test suite for authentication, hashing security, and session management."""

    def setUp(self):
        """Clean up test user state before each test."""
        user = db_get_user_by_email("newhire@talent.io")
        if user:
            db_delete_user(user["id"])

    def tearDown(self):
        """Clean up test user state after each test."""
        user = db_get_user_by_email("newhire@talent.io")
        if user:
            db_delete_user(user["id"])

    def test_password_hashing_and_verification(self):
        """Verifies PBKDF2-HMAC-SHA256 hashing and salt behavior."""
        pwd = "TestSecurePassword123!"
        hashed, salt = _hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(_verify_password(pwd, hashed, salt))
        self.assertFalse(_verify_password("WrongPassword123!", hashed, salt))

    def test_email_validation(self):
        """Tests email format checks."""
        self.assertTrue(validate_email("user@example.com"))
        self.assertTrue(validate_email("recruiter.lead@company.co.in"))
        self.assertFalse(validate_email("invalid-email"))
        self.assertFalse(validate_email("@missinguser.com"))
        self.assertFalse(validate_email(""))

    def test_password_strength(self):
        """Tests password validation rules."""
        is_valid, _ = validate_password_strength("Short1")
        self.assertTrue(is_valid)

        is_valid, msg = validate_password_strength("abc")
        self.assertFalse(is_valid)

        is_valid, msg = validate_password_strength("nociphershere")
        self.assertFalse(is_valid)

    def test_seed_user_authentication(self):
        """Verifies built-in demo credentials log in properly."""
        success, user, msg = authenticate_user("recruiter@resumerank.ai", "Recruiter@2026")
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "Recruiter / Talent Lead")

        # Wrong password
        fail, user_bad, _ = authenticate_user("recruiter@resumerank.ai", "WrongPass123")
        self.assertFalse(fail)
        self.assertIsNone(user_bad)

    def test_user_registration_and_login(self):
        """Tests registering a new user and subsequent login."""
        new_email = "newhire@talent.io"
        new_pwd = "HireTalent2026"
        succ, user, msg = register_user(new_email, new_pwd, "Alice Smith", "Hiring Manager")
        self.assertTrue(succ)
        self.assertEqual(user["full_name"], "Alice Smith")
        self.assertEqual(user["role"], "Hiring Manager")

        # Duplicate registration should fail
        dup_succ, _, _ = register_user(new_email, new_pwd, "Alice Smith", "Hiring Manager")
        self.assertFalse(dup_succ)

        # Log in with newly registered account
        login_succ, login_user, _ = authenticate_user(new_email, new_pwd)
        self.assertTrue(login_succ)
        self.assertEqual(login_user["email"], new_email)

    def test_password_reset_flow(self):
        """Verifies sandbox reset token generation and completion."""
        email = "recruiter@resumerank.ai"
        succ, msg, token = initiate_password_reset(email)
        self.assertTrue(succ)
        self.assertIsNotNone(token)

        new_pass = "UpdatedRecruiter2026"
        reset_succ, reset_msg = complete_password_reset(token, new_pass)
        self.assertTrue(reset_succ)

        # Login with new password
        login_succ, _, _ = authenticate_user(email, new_pass)
        self.assertTrue(login_succ)

        # Reset back to default for other tests
        succ_back, _, token_back = initiate_password_reset(email)
        complete_password_reset(token_back, "Recruiter@2026")


if __name__ == "__main__":
    unittest.main()
