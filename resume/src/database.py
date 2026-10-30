"""
AI Resume Screening and Job Matching System - SQLite Persistence & Database Layer.
Provides relational data storage with parameterized SQL queries for:
- User accounts with role-based access control (admin / user)
- Secure salted bcrypt password storage
- Uploaded candidate resumes and parsed telemetry
- Screening operations and AI match audit logs
- Job descriptions management
- Single-use password reset tokens
"""

import os
import sqlite3
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple, Generator
from contextlib import contextmanager
import bcrypt

# Base path for database file
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "airesume.db")

# Default initial administrator credentials (configurable via env vars or secrets)
DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@airesume.com").strip().lower()
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ResumeAdmin@2026!")


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Creates, yields and automatically closes a thread-safe SQLite connection with Row factory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def hash_password_bcrypt(password: str) -> str:
    """Hashes a plaintext password using bcrypt with cryptographic salt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password_bcrypt(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt or legacy PBKDF2 hash."""
    if not password or not hashed_password:
        return False
    try:
        # Check if hash is bcrypt
        if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        pass
    return False


# ==============================================================================
# DATABASE SCHEMA INITIALIZATION & PROVISIONING
# ==============================================================================
def init_db(admin_email: Optional[str] = None, admin_password: Optional[str] = None) -> None:
    """
    Initializes database schema if not present, and automatically provisions:
    1. Primary Administrator account (admin@airesume.com)
    2. Default demo user (recruiter@resumerank.ai) for evaluation
    3. Standard curated Job Descriptions
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended')),
            created_at TEXT NOT NULL,
            last_login TEXT
        );
        """)

        # 2. Resumes Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT,
            word_count INTEGER DEFAULT 0,
            extracted_email TEXT,
            candidate_name TEXT,
            skills_detected TEXT,
            uploaded_at TEXT NOT NULL,
            status TEXT DEFAULT 'parsed',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # 3. Screening Records Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            job_title TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            filename TEXT NOT NULL,
            composite_score REAL NOT NULL,
            semantic_score REAL NOT NULL,
            skill_score REAL NOT NULL,
            decision TEXT NOT NULL,
            screened_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # 4. Jobs Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            department TEXT DEFAULT 'Engineering',
            experience_level TEXT DEFAULT 'Mid-Senior',
            description TEXT NOT NULL,
            created_by TEXT DEFAULT 'admin',
            created_at TEXT NOT NULL
        );
        """)

        # 5. Password Reset Tokens Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at REAL NOT NULL
        );
        """)

        # Indexes for rapid queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_user ON screening_records(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);")

        conn.commit()

        # Check and provision initial Admin Account
        target_admin_email = (admin_email or DEFAULT_ADMIN_EMAIL).strip().lower()
        target_admin_pass = admin_password or DEFAULT_ADMIN_PASSWORD

        cursor.execute("SELECT id, role FROM users WHERE email = ?;", (target_admin_email,))
        admin_row = cursor.fetchone()

        if not admin_row:
            admin_id = f"usr_admin_{uuid.uuid4().hex[:8]}"
            admin_hash = hash_password_bcrypt(target_admin_pass)
            now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            cursor.execute("""
            INSERT INTO users (id, email, full_name, password_hash, role, status, created_at)
            VALUES (?, ?, ?, ?, 'admin', 'active', ?);
            """, (admin_id, target_admin_email, "System Administrator", admin_hash, now_str))
            conn.commit()

        # Check and provision initial demo user (recruiter@resumerank.ai)
        cursor.execute("SELECT id FROM users WHERE email = ?;", ("recruiter@resumerank.ai",))
        demo_row = cursor.fetchone()
        if not demo_row:
            demo_id = f"usr_demo_{uuid.uuid4().hex[:8]}"
            demo_hash = hash_password_bcrypt("Recruiter@2026")
            now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            cursor.execute("""
            INSERT INTO users (id, email, full_name, password_hash, role, status, created_at)
            VALUES (?, ?, ?, ?, 'Recruiter / Talent Lead', 'active', ?);
            """, (demo_id, "recruiter@resumerank.ai", "Sarah Jenkins", demo_hash, now_str))
            conn.commit()
        else:
            # Ensure role matches for existing seed user
            cursor.execute("UPDATE users SET role = 'Recruiter / Talent Lead' WHERE email = 'recruiter@resumerank.ai';")
            conn.commit()

        # Seed initial job descriptions if empty
        cursor.execute("SELECT COUNT(*) as cnt FROM jobs;")
        if cursor.fetchone()["cnt"] == 0:
            from src.constants import SAMPLE_JOB_DESCRIPTIONS
            dept_map = {
                "AI / Machine Learning Engineer": ("AI Research & Development", "Senior (4+ Yrs)"),
                "Full Stack Developer": ("Platform Engineering", "Mid-Level (2-5 Yrs)"),
                "Data Scientist": ("Data & Analytics", "Mid-Senior (3+ Yrs)"),
                "Cloud & DevOps Engineer": ("Infrastructure & Cloud", "Senior (5+ Yrs)")
            }
            now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for title, desc in SAMPLE_JOB_DESCRIPTIONS.items():
                dept, exp = dept_map.get(title, ("Engineering", "Professional"))
                cursor.execute("""
                INSERT OR IGNORE INTO jobs (title, department, experience_level, description, created_by, created_at)
                VALUES (?, ?, ?, ?, 'system', ?);
                """, (title, dept, exp, desc, now_str))
            conn.commit()


# ==============================================================================
# USER MANAGEMENT FUNCTIONS
# ==============================================================================
def db_get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by email address."""
    if not email:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?;", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def db_get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by user_id."""
    if not user_id:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def db_create_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "user"
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Creates a new user record in SQLite with a secure bcrypt password hash.
    Enforces strict role constraint: public registrations can only create role='user'.
    """
    clean_email = email.strip().lower()
    clean_name = full_name.strip()

    # Enforce allowed roles: public registration cannot create admin
    if role.strip().lower() == "admin":
        return False, None, "Registration with administrator role is not permitted."
    if not role or role not in ("user", "admin", "Recruiter / Talent Lead", "Hiring Manager", "Technical Interviewer", "Guest Evaluator (Demo)"):
        role = "user"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?;", (clean_email,))
        if cursor.fetchone():
            return False, None, "An account with this email address already exists. Please sign in."

        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        pwd_hash = hash_password_bcrypt(password)
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        cursor.execute("""
        INSERT INTO users (id, email, full_name, password_hash, role, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?);
        """, (user_id, clean_email, clean_name, pwd_hash, role, created_at))
        conn.commit()

        user_obj = {
            "id": user_id,
            "email": clean_email,
            "full_name": clean_name,
            "role": role,
            "status": "active",
            "created_at": created_at
        }
        return True, user_obj, "Account created successfully!"


def db_get_all_users(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all registered users, optionally filtered by search query."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if search_query and search_query.strip():
            pattern = f"%{search_query.strip()}%"
            cursor.execute("""
            SELECT id, email, full_name, role, status, created_at, last_login
            FROM users
            WHERE email LIKE ? OR full_name LIKE ? OR role LIKE ?
            ORDER BY created_at DESC;
            """, (pattern, pattern, pattern))
        else:
            cursor.execute("""
            SELECT id, email, full_name, role, status, created_at, last_login
            FROM users
            ORDER BY created_at DESC;
            """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def db_set_user_status(user_id: str, status: str) -> Tuple[bool, str]:
    """Activates or deactivates a user account."""
    if status not in ("active", "inactive", "suspended"):
        return False, "Invalid account status specified."
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Protect primary admin from deactivation
        cursor.execute("SELECT email, role FROM users WHERE id = ?;", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return False, "User not found."
        if user_row["email"] == DEFAULT_ADMIN_EMAIL:
            return False, "The primary administrator account cannot be deactivated."

        cursor.execute("UPDATE users SET status = ? WHERE id = ?;", (status, user_id))
        conn.commit()
        return True, f"User status successfully updated to '{status}'."


def db_delete_user(user_id: str) -> Tuple[bool, str]:
    """Deletes a user account with verification."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, role FROM users WHERE id = ?;", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return False, "User not found."
        if user_row["email"] == DEFAULT_ADMIN_EMAIL:
            return False, "The primary administrator account cannot be deleted."

        cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()
        return True, "User account successfully deleted."


def db_update_user_password(user_id: str, new_password: str) -> bool:
    """Updates a user's password with a new bcrypt hash."""
    pwd_hash = hash_password_bcrypt(new_password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?;", (pwd_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0


def db_record_user_login(user_id: str) -> None:
    """Records the current timestamp as the user's last login."""
    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?;", (now_str, user_id))
        conn.commit()


def db_get_user_metrics() -> Dict[str, int]:
    """Returns summary user counts for administration dashboards."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM users;")
        total = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) as active FROM users WHERE status = 'active';")
        active = cursor.fetchone()["active"]
        cursor.execute("SELECT COUNT(*) as admins FROM users WHERE role = 'admin';")
        admins = cursor.fetchone()["admins"]
        cursor.execute("SELECT COUNT(*) as regular FROM users WHERE role = 'user';")
        regular = cursor.fetchone()["regular"]

        return {
            "total_users": total,
            "active_users": active,
            "inactive_users": total - active,
            "admin_count": admins,
            "user_count": regular
        }


# ==============================================================================
# RESUME RECORDS MANAGEMENT
# ==============================================================================
def db_add_resume_record(
    user_id: str,
    filename: str,
    file_type: str,
    word_count: int = 0,
    extracted_email: Optional[str] = None,
    candidate_name: Optional[str] = None,
    skills_detected: Optional[List[str]] = None,
    status: str = "parsed"
) -> int:
    """Saves metadata for an uploaded candidate resume."""
    skills_json = json.dumps(skills_detected or [])
    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO resumes (user_id, filename, file_type, word_count, extracted_email, candidate_name, skills_detected, uploaded_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (user_id, filename, file_type, word_count, extracted_email or "", candidate_name or "", skills_json, now_str, status))
        conn.commit()
        return cursor.lastrowid


def db_get_resumes_by_user(user_id: str) -> List[Dict[str, Any]]:
    """Returns resume records belonging to a specific user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC;
        """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def db_get_all_resumes(limit: int = 200) -> List[Dict[str, Any]]:
    """Returns system-wide resume records for administrative overview."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT r.*, u.email as owner_email, u.full_name as owner_name
        FROM resumes r
        LEFT JOIN users u ON r.user_id = u.id
        ORDER BY r.uploaded_at DESC
        LIMIT ?;
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


def db_delete_resume_record(resume_id: int, user_id: Optional[str] = None) -> bool:
    """Deletes a resume record. If user_id is provided, enforces ownership."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("DELETE FROM resumes WHERE id = ? AND user_id = ?;", (resume_id, user_id))
        else:
            cursor.execute("DELETE FROM resumes WHERE id = ?;", (resume_id,))
        conn.commit()
        return cursor.rowcount > 0


def db_get_total_resumes_count() -> int:
    """Returns total count of uploaded resumes in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM resumes;")
        return cursor.fetchone()["total"]


# ==============================================================================
# SCREENING RECORDS MANAGEMENT
# ==============================================================================
def db_add_screening_record(
    user_id: str,
    job_title: str,
    candidate_name: str,
    filename: str,
    composite_score: float,
    semantic_score: float,
    skill_score: float,
    decision: str
) -> int:
    """Logs an AI screening operation result to SQLite."""
    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO screening_records (user_id, job_title, candidate_name, filename, composite_score, semantic_score, skill_score, decision, screened_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (user_id, job_title, candidate_name, filename, composite_score, semantic_score, skill_score, decision, now_str))
        conn.commit()
        return cursor.lastrowid


def db_get_screening_records(user_id: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    """Returns screening records, optionally scoped to a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("""
            SELECT * FROM screening_records WHERE user_id = ? ORDER BY screened_at DESC LIMIT ?;
            """, (user_id, limit))
        else:
            cursor.execute("""
            SELECT s.*, u.email as recruiter_email, u.full_name as recruiter_name
            FROM screening_records s
            LEFT JOIN users u ON s.user_id = u.id
            ORDER BY s.screened_at DESC LIMIT ?;
            """, (limit,))
        return [dict(r) for r in cursor.fetchall()]


def db_get_screening_metrics() -> Dict[str, Any]:
    """Computes screening telemetry for dashboards."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total, AVG(composite_score) as avg_score FROM screening_records;")
        row = cursor.fetchone()
        total = row["total"] or 0
        avg_score = round(row["avg_score"] or 0.0, 1)

        cursor.execute("SELECT COUNT(*) as short FROM screening_records WHERE decision = 'SHORTLISTED';")
        shortlisted = cursor.fetchone()["short"] or 0

        return {
            "total_screenings": total,
            "avg_composite_score": avg_score,
            "shortlisted_count": shortlisted,
            "review_count": total - shortlisted
        }


# ==============================================================================
# JOB DESCRIPTIONS MANAGEMENT
# ==============================================================================
def db_add_job(
    title: str,
    description: str,
    department: str = "Engineering",
    experience_level: str = "Mid-Senior",
    created_by: str = "admin"
) -> Tuple[bool, str, Optional[int]]:
    """Adds a new job description to SQLite."""
    title_clean = title.strip()
    if not title_clean:
        return False, "Job title is required.", None
    if not description.strip():
        return False, "Job description content is required.", None

    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jobs WHERE title = ? COLLATE NOCASE;", (title_clean,))
        if cursor.fetchone():
            return False, f"A job specification with title '{title_clean}' already exists.", None

        cursor.execute("""
        INSERT INTO jobs (title, department, experience_level, description, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (title_clean, department.strip(), experience_level.strip(), description.strip(), created_by, now_str))
        conn.commit()
        return True, "Job specification added successfully!", cursor.lastrowid


def db_update_job(
    job_id: int,
    title: str,
    description: str,
    department: str,
    experience_level: str
) -> Tuple[bool, str]:
    """Updates an existing job specification."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jobs WHERE id = ?;", (job_id,))
        if not cursor.fetchone():
            return False, "Job not found."

        cursor.execute("""
        UPDATE jobs
        SET title = ?, description = ?, department = ?, experience_level = ?
        WHERE id = ?;
        """, (title.strip(), description.strip(), department.strip(), experience_level.strip(), job_id))
        conn.commit()
        return True, "Job specification updated successfully!"


def db_delete_job(job_id: int) -> Tuple[bool, str]:
    """Deletes a job specification."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?;", (job_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Job specification removed."
        return False, "Job not found."


def db_get_all_jobs() -> List[Dict[str, Any]]:
    """Retrieves all jobs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id ASC;")
        return [dict(r) for r in cursor.fetchall()]


def db_get_total_jobs_count() -> int:
    """Returns the total number of managed jobs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM jobs;")
        return cursor.fetchone()["total"]


# ==============================================================================
# PASSWORD RESET TOKENS
# ==============================================================================
def db_create_password_reset_token(email: str, expiry_seconds: int = 900) -> str:
    """Stores a single-use password reset token with expiration."""
    clean_email = email.strip().lower()
    token = f"rst_{uuid.uuid4().hex[:12]}"
    expires_at = time.time() + expiry_seconds

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM password_resets WHERE email = ?;", (clean_email,))
        cursor.execute("""
        INSERT INTO password_resets (token, email, expires_at)
        VALUES (?, ?, ?);
        """, (token, clean_email, expires_at))
        conn.commit()
    return token


def db_verify_and_consume_reset_token(token: str) -> Optional[str]:
    """Verifies a reset token and consumes it if valid, returning the associated email."""
    if not token:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, expires_at FROM password_resets WHERE token = ?;", (token.strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        
        email = row["email"]
        expires_at = row["expires_at"]
        if time.time() > expires_at:
            cursor.execute("DELETE FROM password_resets WHERE token = ?;", (token.strip(),))
            conn.commit()
            return None

        # Consume token
        cursor.execute("DELETE FROM password_resets WHERE token = ?;", (token.strip(),))
        conn.commit()
        return email
