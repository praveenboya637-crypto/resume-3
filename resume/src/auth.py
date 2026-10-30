"""
ResumeRank AI - Authentication, Authorization & Session Management Module.
Supports:
- Persistent SQLite-backed authentication with bcrypt password hashing
- Strict Role-Based Access Control (RBAC): 'admin' and 'user'
- Admin account auto-provisioning
- Account activation/deactivation checks
- Supabase Auth via REST API when configured (optional enterprise mode)
- Single-use password reset tokens
Never stores plaintext passwords.
"""

import os
import re
import json
import time
import uuid
import hashlib
import hmac
from typing import Dict, Any, Optional, Tuple, List
import requests
import bcrypt

from src.database import (
    init_db,
    db_get_user_by_email,
    db_get_user_by_id,
    db_create_user,
    db_update_user_password,
    db_record_user_login,
    db_create_password_reset_token,
    db_verify_and_consume_reset_token,
    hash_password_bcrypt,
    verify_password_bcrypt,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD
)

# Ensure database is initialized on module load
try:
    init_db()
except Exception as _e:
    pass

# Supabase Auth REST Endpoints (if configured)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", os.environ.get("SUPABASE_KEY", ""))

# Try reading from streamlit secrets if available
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        if not SUPABASE_URL and "SUPABASE_URL" in st.secrets:
            SUPABASE_URL = st.secrets["SUPABASE_URL"]
        if not SUPABASE_ANON_KEY:
            if "SUPABASE_ANON_KEY" in st.secrets:
                SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
            elif "SUPABASE_KEY" in st.secrets:
                SUPABASE_ANON_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    pass

# Supported Roles
ROLES = [
    "user",
    "admin"
]

# Legacy display roles for backward compatibility
DISPLAY_ROLES = [
    "Recruiter / Talent Lead",
    "Hiring Manager",
    "Technical Interviewer",
    "Guest Evaluator (Demo)"
]

# In-memory store for active password reset tokens fallback
_RESET_TOKENS: Dict[str, Dict[str, Any]] = {}


def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generates a secure PBKDF2-HMAC-SHA256 hash with cryptographic salt (maintained for compatibility)."""
    if salt is None:
        salt = uuid.uuid4().hex
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100_000)
    return derived.hex(), salt


def _verify_password(password: str, stored_hash: str, salt: Optional[str] = None) -> bool:
    """Verifies a password against bcrypt hash or legacy PBKDF2 hash."""
    if not password or not stored_hash:
        return False
    # Check bcrypt first
    if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False
    # Fallback to PBKDF2 if salt provided
    if salt:
        test_hash, _ = _hash_password(password, salt)
        return hmac.compare_digest(test_hash, stored_hash)
    return False


# In-memory user store mirror for existing test compatibility
_recruiter_hash, _recruiter_salt = _hash_password("Recruiter@2026", "salt_recruiter_01")
_manager_hash, _manager_salt = _hash_password("Manager@2026", "salt_manager_01")
_guest_hash, _guest_salt = _hash_password("Guest@2026", "salt_guest_01")

_LOCAL_USER_DB: Dict[str, Dict[str, Any]] = {
    "recruiter@resumerank.ai": {
        "id": "usr_recruiter_001",
        "email": "recruiter@resumerank.ai",
        "full_name": "Sarah Jenkins",
        "role": "Recruiter / Talent Lead",
        "hash": _recruiter_hash,
        "salt": _recruiter_salt,
        "created_at": "2026-01-15T09:00:00Z",
        "is_demo_seed": True
    },
    "manager@resumerank.ai": {
        "id": "usr_manager_002",
        "email": "manager@resumerank.ai",
        "full_name": "David Chen",
        "role": "Hiring Manager",
        "hash": _manager_hash,
        "salt": _manager_salt,
        "created_at": "2026-02-01T10:30:00Z",
        "is_demo_seed": True
    },
    "guest@resumerank.ai": {
        "id": "usr_guest_003",
        "email": "guest@resumerank.ai",
        "full_name": "Hackathon Judge",
        "role": "Guest Evaluator (Demo)",
        "hash": _guest_hash,
        "salt": _guest_salt,
        "created_at": "2026-03-01T12:00:00Z",
        "is_demo_seed": True
    }
}


def is_supabase_configured() -> bool:
    """Checks whether real Supabase Auth credentials are provided."""
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY and "supabase.co" in SUPABASE_URL)


def get_auth_mode_info() -> Dict[str, Any]:
    """Returns metadata about the active authentication provider."""
    if is_supabase_configured():
        masked_key = SUPABASE_ANON_KEY[:6] + "..." + SUPABASE_ANON_KEY[-4:] if len(SUPABASE_ANON_KEY) > 10 else "***"
        return {
            "mode": "supabase",
            "provider_name": "Supabase Cloud Auth",
            "configured": True,
            "url": SUPABASE_URL,
            "masked_key": masked_key,
            "badge": "⚡ Live Supabase Auth Active"
        }
    return {
        "mode": "sqlite",
        "provider_name": "SQLite Persistent Auth & RBAC",
        "configured": True,
        "badge": "🔒 SQLite Persistent Auth (Bcrypt)",
        "notes": (
            "Running in secure persistent SQLite mode with salted Bcrypt password hashing. "
            "Separate User and Admin portals with strict role-based access control."
        )
    }


def validate_email(email: str) -> bool:
    """Validates email format."""
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email.strip()))


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Checks password strength criteria."""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, "Strong"


# ==============================================================================
# LOGIN RATE LIMITING (SECURITY LAYER)
# ==============================================================================
_FAILED_LOGIN_ATTEMPTS: Dict[str, List[float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes


def is_rate_limited(email: str) -> Tuple[bool, int]:
    """
    Checks if an email is temporarily locked out due to excessive failed attempts.
    Returns: (is_locked: bool, retry_after_seconds: int)
    """
    clean_email = email.strip().lower()
    now = time.time()
    attempts = _FAILED_LOGIN_ATTEMPTS.get(clean_email, [])
    # Filter attempts within sliding lockout window
    recent_attempts = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
    _FAILED_LOGIN_ATTEMPTS[clean_email] = recent_attempts

    if len(recent_attempts) >= MAX_FAILED_ATTEMPTS:
        retry_after = int(LOCKOUT_DURATION_SECONDS - (now - recent_attempts[0]))
        return True, max(1, retry_after)
    return False, 0


def record_failed_login(email: str) -> None:
    """Records a failed login attempt for the given email."""
    clean_email = email.strip().lower()
    now = time.time()
    if clean_email not in _FAILED_LOGIN_ATTEMPTS:
        _FAILED_LOGIN_ATTEMPTS[clean_email] = []
    _FAILED_LOGIN_ATTEMPTS[clean_email].append(now)


def clear_failed_logins(email: str) -> None:
    """Resets failed login attempts after successful authentication."""
    clean_email = email.strip().lower()
    _FAILED_LOGIN_ATTEMPTS.pop(clean_email, None)


def reset_all_rate_limits() -> None:
    """Clears all rate limit state (useful for test resets)."""
    _FAILED_LOGIN_ATTEMPTS.clear()


# ==============================================================================
# AUTHENTICATION & LOGIN
# ==============================================================================
def authenticate_user(
    email: str,
    password: str,
    required_role: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Authenticates a user via persistent SQLite (or Supabase if configured).
    Enforces role separation if required_role is specified ('admin' or 'user').
    Implements rate limiting protection against brute-force attacks.
    Returns: (success: bool, user_data: Optional[dict], message: str)
    """
    email = email.strip().lower()
    if not validate_email(email):
        return False, None, "Invalid email address format."
    if not password:
        return False, None, "Password cannot be empty."

    # Enforce Rate Limiting Check
    is_locked, retry_after = is_rate_limited(email)
    if is_locked:
        return False, None, f"Too many failed login attempts. Account temporarily locked for security. Please try again in {retry_after} seconds."

    # 1. Supabase Mode (optional cloud override)
    if is_supabase_configured():
        try:
            endpoint = f"{SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }
            payload = {"email": email, "password": password}
            response = requests.post(endpoint, headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                data = response.json()
                sb_user = data.get("user", {})
                role = sb_user.get("user_metadata", {}).get("role", "user")
                if required_role and role != required_role:
                    record_failed_login(email)
                    return False, None, f"Access Denied: Account does not have '{required_role}' privileges."
                clear_failed_logins(email)
                user_obj = {
                    "id": sb_user.get("id"),
                    "email": sb_user.get("email"),
                    "full_name": sb_user.get("user_metadata", {}).get("full_name", email.split("@")[0].title()),
                    "role": role,
                    "status": "active",
                    "is_authenticated": True,
                    "access_token": data.get("access_token"),
                    "provider": "supabase"
                }
                return True, user_obj, "Successfully authenticated with Supabase."
            else:
                record_failed_login(email)
                err_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_data.get("error_description") or err_data.get("msg") or "Invalid email or password."
                return False, None, f"Supabase Auth Error: {err_msg}"
        except Exception as e:
            return False, None, f"Could not reach Supabase Auth server: {str(e)}"

    # 2. SQLite Persistent Authentication
    user = db_get_user_by_email(email)

    # Check memory fallback for seed accounts if not found in db
    if not user and email in _LOCAL_USER_DB:
        user = _LOCAL_USER_DB[email]

    if not user:
        record_failed_login(email)
        return False, None, "No account found with this email. Please check your spelling or register."

    # Check account status
    status = user.get("status", "active")
    if status != "active":
        record_failed_login(email)
        return False, None, f"Account is {status}. Please contact the administrator."

    # Verify password with bcrypt or legacy PBKDF2
    password_hash = user.get("password_hash") or user.get("hash")
    salt = user.get("salt")
    is_valid = _verify_password(password, password_hash, salt)

    if not is_valid:
        record_failed_login(email)
        return False, None, "Incorrect password. Please try again."

    user_role = user.get("role", "user")

    # Role Enforcement Checks
    if required_role:
        if required_role == "admin" and user_role != "admin":
            record_failed_login(email)
            return False, None, "Access Denied: Administrator privileges required."
        if required_role == "user" and user_role == "admin":
            return False, None, "Administrator credentials detected. Please sign in via the Admin Login Portal."

    # Authentication succeeded - clear failed attempts counter
    clear_failed_logins(email)

    # Update last login timestamp in SQLite
    if "id" in user:
        try:
            db_record_user_login(user["id"])
        except Exception:
            pass

    user_obj = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user_role,
        "status": status,
        "is_authenticated": True,
        "session_token": uuid.uuid4().hex,
        "login_time": time.time(),
        "provider": "sqlite"
    }
    return True, user_obj, "Login successful."


# ==============================================================================
# USER REGISTRATION
# ==============================================================================
def register_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "user"
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Registers a new regular user.
    SECURITY: Enforces role='user'. Normal registration can NEVER create administrators.
    """
    email = email.strip().lower()
    full_name = full_name.strip()
    if not validate_email(email):
        return False, None, "Invalid email address format."
    if not full_name:
        return False, None, "Full name is required."

    is_strong, pwd_err = validate_password_strength(password)
    if not is_strong:
        return False, None, pwd_err

    # Strict RBAC: Public registration cannot create administrators
    if role.strip().lower() == "admin":
        return False, None, "Registration with administrator role is not permitted."
    if role not in ROLES and role not in DISPLAY_ROLES:
        role = "user"
    assigned_role = role

    # 1. Supabase Mode
    if is_supabase_configured():
        try:
            endpoint = f"{SUPABASE_URL.rstrip('/')}/auth/v1/signup"
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "email": email,
                "password": password,
                "data": {
                    "full_name": full_name,
                    "role": assigned_role
                }
            }
            response = requests.post(endpoint, headers=headers, json=payload, timeout=8)
            if response.status_code in (200, 201):
                data = response.json()
                sb_user = data.get("user") or data
                user_obj = {
                    "id": sb_user.get("id"),
                    "email": sb_user.get("email"),
                    "full_name": full_name,
                    "role": assigned_role,
                    "status": "active",
                    "access_token": data.get("access_token"),
                    "provider": "supabase"
                }
                return True, user_obj, "Account created successfully with Supabase!"
            else:
                err_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_data.get("error_description") or err_data.get("msg") or "Registration failed."
                return False, None, f"Supabase Error: {err_msg}"
        except Exception as e:
            return False, None, f"Failed to register with Supabase: {str(e)}"

    # 2. SQLite Persistent Mode
    succ, user_data, msg = db_create_user(email, password, full_name, role=assigned_role)
    if succ and user_data:
        # Also mirror in memory for legacy test harness
        _LOCAL_USER_DB[email] = {
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "role": user_data["role"],
            "hash": hash_password_bcrypt(password),
            "salt": "",
            "created_at": user_data["created_at"],
            "is_demo_seed": False
        }
        user_obj = {
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "role": user_data["role"],
            "status": "active",
            "is_authenticated": True,
            "session_token": uuid.uuid4().hex,
            "login_time": time.time(),
            "provider": "sqlite"
        }
        return True, user_obj, "Account registered successfully! You are now logged in."

    return False, None, msg


# ==============================================================================
# PASSWORD RESET WORKFLOW
# ==============================================================================
def initiate_password_reset(email: str) -> Tuple[bool, str, Optional[str]]:
    """Generates a secure password reset token stored in SQLite."""
    email = email.strip().lower()
    if not validate_email(email):
        return False, "Invalid email format.", None

    user = db_get_user_by_email(email)
    if not user and email in _LOCAL_USER_DB:
        user = _LOCAL_USER_DB[email]

    if not user:
        return False, "No registered account found with this email address.", None

    token = db_create_password_reset_token(email)
    # Mirror in memory for backward compatibility
    _RESET_TOKENS[token] = {
        "email": email,
        "expires_at": time.time() + 900
    }
    return True, f"Reset token generated! For local demonstration, your token is: {token}", token


def complete_password_reset(token: str, new_password: str) -> Tuple[bool, str]:
    """Completes password reset using token and updates SQLite record."""
    token = token.strip()
    if not token:
        return False, "Invalid reset token."

    is_strong, msg = validate_password_strength(new_password)
    if not is_strong:
        return False, msg

    # Verify and consume token from SQLite
    email = db_verify_and_consume_reset_token(token)

    # Fallback to memory
    if not email and token in _RESET_TOKENS:
        token_data = _RESET_TOKENS[token]
        if time.time() <= token_data["expires_at"]:
            email = token_data["email"]
        del _RESET_TOKENS[token]

    if not email:
        return False, "Invalid or expired reset token."

    user = db_get_user_by_email(email)
    if user:
        db_update_user_password(user["id"], new_password)
        if email in _LOCAL_USER_DB:
            pwd_hash, pwd_salt = _hash_password(new_password)
            _LOCAL_USER_DB[email]["hash"] = pwd_hash
            _LOCAL_USER_DB[email]["salt"] = pwd_salt
        return True, "Password has been successfully updated! You can now log in with your new password."

    return False, "Account associated with token no longer exists."


# ==============================================================================
# AUTHORIZATION HELPERS
# ==============================================================================
def is_admin(user: Optional[Dict[str, Any]]) -> bool:
    """Verifies that user is authenticated and holds administrator privileges."""
    return bool(user and user.get("is_authenticated", False) and str(user.get("role", "")).strip().lower() == "admin")


def is_user(user: Optional[Dict[str, Any]]) -> bool:
    """Verifies that user is authenticated with a regular non-admin user role."""
    return bool(user and user.get("is_authenticated", False) and str(user.get("role", "")).strip().lower() != "admin")
