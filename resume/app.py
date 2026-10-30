"""
AI Resume Screening and Job Matching System
Next-Generation SaaS Talent Intelligence Platform for National Hackathons & Production.
Features:
- Premium Navy, Electric Blue, Violet, Cyan design system with Dark/Light modes
- High-converting Startup Landing Page ("Find the Right Talent. Faster with AI.")
- Interactive Visual Resume-Job Matching Simulation Graphic
- Branded Split-Screen Authentication (PBKDF2/SHA-256 Salted Sandbox & Supabase Cloud)
- Executive Recruiter Dashboard with Live Telemetry, Activity Stream & Charts
- Two-Column Screening Studio (PDF/DOCX batch parsing & JD Intelligence)
- Candidate Rankings Leaderboard with Podium Styling & XAI Grounded Evidence
- Side-by-Side Candidate Head-to-Head Comparison
- Personalized Skill Gap Analysis & Project-Based Upskilling Roadmaps
- Dedicated Analytics & Reports with Formula-Protected CSV Export
- Recruiter Profile & Settings with CPU Local Inference Telemetry
"""

import os
import time
import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional

from src.constants import (
    DEFAULT_MODEL_NAME,
    DEFAULT_SEMANTIC_WEIGHT,
    DEFAULT_SKILL_WEIGHT,
    DEFAULT_SHORTLIST_THRESHOLD,
    SAMPLE_JOB_DESCRIPTIONS,
    ETHICAL_DISCLAIMER
)
from src.parsers import parse_resume
from src.embeddings import load_sentence_transformer_model, batch_compute_similarity
from src.ranker import rank_resumes
from src.utils import (
    generate_csv_report,
    validate_job_description,
    create_sample_files,
    sanitize_filename,
    validate_uploaded_files
)
from src.auth import (
    authenticate_user,
    register_user,
    initiate_password_reset,
    complete_password_reset,
    get_auth_mode_info,
    is_supabase_configured,
    is_admin,
    is_user,
    ROLES
)
from src.database import (
    init_db,
    db_add_resume_record,
    db_add_screening_record,
    db_get_total_resumes_count,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD
)
from src.admin_view import render_admin_dashboard
from src.jd_analyzer import analyze_job_description
from src.learning_recommender import get_recommendations_for_missing_skills
from src.profile_extractor import extract_candidate_profile_facts, categorize_explanation_elements
from src.styles import get_css, get_logo_svg
from src.resume_builder_view import render_resume_builder_page
from src.ui_components import (
    render_brand_badge,
    render_navbar_html,
    render_visual_matching_showcase,
    render_stat_card_html,
    render_footer_html
)

# Initialize persistent SQLite database & auto-provision administrator
init_db()


# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="AI Resume Screening and Job Matching System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Landing Page"
if "user" not in st.session_state:
    st.session_state.user = None
if "ranked_results" not in st.session_state:
    st.session_state.ranked_results = None
if "summary_df" not in st.session_state:
    st.session_state.summary_df = None
if "parsed_resumes" not in st.session_state:
    st.session_state.parsed_resumes = None
if "is_demo_data" not in st.session_state:
    st.session_state.is_demo_data = False
if "jd_text_input" not in st.session_state:
    st.session_state.jd_text_input = SAMPLE_JOB_DESCRIPTIONS["AI / Machine Learning Engineer"]
if "selected_preset" not in st.session_state:
    st.session_state.selected_preset = "AI / Machine Learning Engineer"
if "semantic_wt" not in st.session_state:
    st.session_state.semantic_wt = DEFAULT_SEMANTIC_WEIGHT
if "shortlist_cutoff" not in st.session_state:
    st.session_state.shortlist_cutoff = DEFAULT_SHORTLIST_THRESHOLD
if "recent_activity" not in st.session_state:
    st.session_state.recent_activity = [
        {"time": "10m ago", "title": "System Initialized", "desc": "Sentence-Transformers 384-D model ready on CPU", "tag": "READY", "color": "#10B981"},
        {"time": "30m ago", "title": "Role Profile Configured", "desc": "Target: Senior AI / Machine Learning Engineer", "tag": "CONFIG", "color": "#38BDF8"}
    ]

# Inject Global Modern SaaS CSS
st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)


# --- Cached Inference Model Loader ---
@st.cache_resource(show_spinner=False)
def get_cached_embedding_model():
    """Loads and caches the SentenceTransformer model in memory."""
    model, backend = load_sentence_transformer_model(DEFAULT_MODEL_NAME)
    return model, backend


# Ensure sample resumes directory exists
sample_resumes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data", "resumes")
try:
    create_sample_files(sample_resumes_dir)
except Exception:
    pass


# --- Helper: Render Skill Badges ---
def render_skill_badges(skills: List[str], badge_type: str = "matched") -> str:
    """Renders HTML badge pills with appropriate styling."""
    if not skills:
        return "<span style='color: #64748B; font-style: italic; font-size: 13px;'>None detected</span>"
    class_map = {
        "matched": "badge-matched",
        "missing": "badge-missing",
        "bonus": "badge-bonus",
        "neutral": "badge-neutral"
    }
    pill_cls = class_map.get(badge_type, "badge-neutral")
    return "".join([f"<span class='badge-pill {pill_cls}'>{s}</span>" for s in skills])


# --- Helper: Quick Demo Data Loader ---
def load_demo_data_action(model_instance, s_wt, k_wt, s_cut):
    """Loads sample resumes from disk, computes embeddings, and runs ranking."""
    loaded_resumes = []
    if os.path.exists(sample_resumes_dir):
        for fname in sorted(os.listdir(sample_resumes_dir)):
            if fname.endswith((".pdf", ".docx")):
                fpath = os.path.join(sample_resumes_dir, fname)
                parsed = parse_resume(fpath, filename=fname)
                loaded_resumes.append(parsed)
    if loaded_resumes:
        st.session_state.parsed_resumes = loaded_resumes
        raw_sims = batch_compute_similarity(loaded_resumes, st.session_state.jd_text_input, model=model_instance)
        ranked_all, df_summary = rank_resumes(
            parsed_resumes=loaded_resumes,
            jd_text=st.session_state.jd_text_input,
            semantic_similarities=raw_sims,
            semantic_weight=s_wt,
            skill_weight=k_wt,
            shortlist_threshold=s_cut
        )
        st.session_state.ranked_results = ranked_all
        st.session_state.summary_df = df_summary
        st.session_state.is_demo_data = True
        
        # Sync demo data to persistent SQLite database
        try:
            curr_uid = st.session_state.user.get("id") if (st.session_state.user and st.session_state.user.get("id")) else "demo_candidate_pool"
            for r in loaded_resumes:
                db_add_resume_record(
                    user_id=curr_uid,
                    filename=r.get("filename", "resume.pdf"),
                    file_type=r.get("file_type", "pdf"),
                    word_count=r.get("word_count", 0),
                    extracted_email=r.get("email", ""),
                    candidate_name=r.get("candidate_name", ""),
                    skills_detected=r.get("skills", []),
                    status="parsed"
                )
            for item in ranked_all:
                db_add_screening_record(
                    user_id=curr_uid,
                    job_title=st.session_state.selected_preset or "AI / Machine Learning Engineer",
                    candidate_name=item.get("candidate_name", "Unknown"),
                    filename=item.get("filename", ""),
                    composite_score=float(item.get("composite_score", 0)),
                    semantic_score=float(item.get("semantic_score", 0)),
                    skill_score=float(item.get("skill_score", 0)),
                    decision="SHORTLISTED" if item.get("is_shortlisted") else "REVIEW"
                )
        except Exception:
            pass

        # Add to recent activity
        st.session_state.recent_activity.insert(0, {
            "time": "Just now",
            "title": f"Screened {len(loaded_resumes)} Demo Resumes",
            "desc": f"Top Candidate: {ranked_all[0]['candidate_name']} ({ranked_all[0]['composite_score']}%)",
            "tag": "SCREENED",
            "color": "#10B981"
        })
        return True
    return False


# ==============================================================================
# SIDEBAR NAVIGATION & CONTROLS
# ==============================================================================
with st.sidebar:
    # Sidebar Brand Header with SVG Logo
    st.markdown(
        f"<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border-color);'>"
        f"<div>{get_logo_svg(size=36, show_glow=False, prefix='sidebar')}</div>"
        f"<div>"
        f"<div style='font-size: 16px; font-weight: 800; letter-spacing: -0.4px; color: #F8FAFC;'>AI Resume System</div>"
        f"<div style='font-size: 11px; color: #38BDF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;'>Talent Intelligence</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Dynamic User Profile & Role-Based Navigation
    curr_user = st.session_state.user
    auth_info = get_auth_mode_info()

    if curr_user and curr_user.get("is_authenticated"):
        if is_admin(curr_user):
            # Admin Theme: Purple / Slate Command Center
            st.markdown(f"""
            <div class='admin-card' style='margin-bottom: 14px; padding: 12px 14px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span class='admin-badge'>🛡️ System Administrator</span>
                    <span style='font-size: 10px; color: #C084FC; font-weight: 700;'>SECURE</span>
                </div>
                <div style='font-size: 14px; font-weight: 800; color: #FFFFFF; margin-top: 6px;'>{curr_user.get("full_name")}</div>
                <div style='font-size: 11px; color: #CBD5E1;'>{curr_user.get("email")}</div>
            </div>
            """, unsafe_allow_html=True)

            pages = [
                "🛡️ Admin Dashboard",
                "⚡ Resume Screening",
                "🎯 Job Matching",
                "📝 Resume Builder",
                "🏠 Landing Page"
            ]

            if st.button("🚪 Admin Sign Out", use_container_width=True, key="admin_sidebar_logout"):
                st.session_state.user = None
                st.session_state.current_page = "🏠 Landing Page"
                st.rerun()

        else:
            # User Theme: Modern Electric Blue / Cyan Talent Intelligence
            st.markdown(f"""
            <div class='user-portal-badge' style='margin-bottom: 14px; padding: 12px 14px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='font-size: 10px; text-transform: uppercase; color: #38BDF8; font-weight: 800; letter-spacing: 0.5px;'>👤 Candidate / Recruiter</div>
                    <div style='font-size: 10px; color: #34D399; font-weight: 700;'>ACTIVE</div>
                </div>
                <div style='font-size: 14px; font-weight: 700; color: #F8FAFC; margin-top: 4px;'>{curr_user.get("full_name")}</div>
                <div style='font-size: 11px; color: #94A3B8;'>{curr_user.get("role")}</div>
            </div>
            """, unsafe_allow_html=True)

            pages = [
                "📊 Dashboard",
                "📝 Resume Builder",
                "⚡ Resume Screening",
                "🎯 Job Matching",
                "🏆 Candidate Rankings",
                "🗺️ Skill Gap Analysis",
                "⚖️ Candidate Comparison",
                "📈 Analytics",
                "📄 Reports",
                "⚙️ Profile and Settings",
                "🏠 Landing Page"
            ]

            if st.button("🚪 Sign Out", use_container_width=True, key="user_sidebar_logout"):
                st.session_state.user = None
                st.session_state.current_page = "🏠 Landing Page"
                st.rerun()

    else:
        # Guest Mode: Modern Gold / Amber Notice
        st.markdown(f"""
        <div style='background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 12px 14px; margin-bottom: 14px;'>
            <div style='font-size: 10px; text-transform: uppercase; color: #FBBF24; font-weight: 800;'>🔓 Guest Portal</div>
            <div style='font-size: 12px; color: #E2E8F0; margin-top: 4px;'>Sign in via Candidate or Administrator portals to access full features.</div>
        </div>
        """, unsafe_allow_html=True)

        pages = [
            "🏠 Landing Page",
            "👤 User Login",
            "📝 User Registration",
            "🛡️ Admin Login",
            "📝 Resume Builder"
        ]

    # Ensure current page is valid for current role
    if st.session_state.current_page not in pages:
        if st.session_state.current_page == "🛡️ Admin Dashboard" and not is_admin(curr_user):
            st.session_state.current_page = "🏠 Landing Page"
        elif curr_user and curr_user.get("is_authenticated"):
            st.session_state.current_page = pages[0]
        else:
            st.session_state.current_page = "🏠 Landing Page"

    current_idx = pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0
    selected_page = st.radio("Navigation", pages, index=current_idx)
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()

    st.markdown("---")

    # Scoring Weights Controls
    st.markdown("#### ⚖️ Scoring Formula Weights")
    semantic_wt = st.slider(
        "Semantic Weight (Sentence-Transformers)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.semantic_wt,
        step=0.05,
        help="Weight assigned to 384-dimensional dense semantic embeddings."
    )
    st.session_state.semantic_wt = semantic_wt
    skill_wt = round(1.0 - semantic_wt, 2)
    st.caption(f"Technical Skill Overlap Weight: **{skill_wt * 100:.0f}%**")

    shortlist_cutoff = st.slider(
        "Shortlist Cutoff (%)",
        min_value=40.0,
        max_value=90.0,
        value=st.session_state.shortlist_cutoff,
        step=5.0,
        help="Candidates at or above this percentage are flagged as Shortlisted."
    )
    st.session_state.shortlist_cutoff = shortlist_cutoff

    st.markdown("---")

    # Inference Engine Telemetry
    with st.spinner("Checking AI Engine..."):
        model, model_backend = get_cached_embedding_model()

    if model_backend == "sentence-transformers":
        st.markdown(f"""
        <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 10px 12px;'>
            <div style='font-size: 11px; font-weight: 800; color: #34D399; text-transform: uppercase;'>🟢 Inference Engine Online</div>
            <div style='font-size: 12px; color: #E2E8F0; margin-top: 3px;'>Model: <code>all-MiniLM-L6-v2</code></div>
            <div style='font-size: 11px; color: #94A3B8; margin-top: 2px;'>Local CPU &middot; Zero API Cost &middot; 100% Private</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("🟡 **Inference Active**: `TF-IDF + Cosine` (Fallback)")

    st.markdown("<br>", unsafe_allow_html=True)

    # Theme Switcher
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        if st.button("🌙 Dark", use_container_width=True, type="primary" if st.session_state.theme == "dark" else "secondary"):
            st.session_state.theme = "dark"
            st.rerun()
    with t_col2:
        if st.button("☀️ Light", use_container_width=True, type="primary" if st.session_state.theme == "light" else "secondary"):
            st.session_state.theme = "light"
            st.rerun()

    # Reset State Action
    if st.button("🔄 Reset Screening State", use_container_width=True):
        st.session_state.ranked_results = None
        st.session_state.summary_df = None
        st.session_state.parsed_resumes = None
        st.session_state.is_demo_data = False
        st.session_state.recent_activity.insert(0, {
            "time": "Just now",
            "title": "Screening Session Cleared",
            "desc": "All candidate files and rankings reset",
            "tag": "RESET",
            "color": "#F43F5E"
        })
        st.success("Screening session cleared.")
        time.sleep(0.3)
        st.rerun()


# ==============================================================================
# SERVER-SIDE ROLE-BASED ACCESS CONTROL (RBAC) GUARD
# ==============================================================================
active_user = st.session_state.user
is_auth = bool(active_user and active_user.get("is_authenticated"))

# Administrator page protection
if st.session_state.current_page == "🛡️ Admin Dashboard":
    if not (is_auth and is_admin(active_user)):
        st.error("⛔ Access Denied: Administrator privileges required to access the Admin Command Center.")
        st.session_state.current_page = "🛡️ Admin Login"
        time.sleep(0.5)
        st.rerun()

# User protected pages (e.g. Profile & Settings)
PROTECTED_USER_PAGES = {
    "⚙️ Profile and Settings"
}
if st.session_state.current_page in PROTECTED_USER_PAGES and not is_auth:
    st.warning("🔒 Please sign in to access your Candidate / Recruiter Account.")
    st.session_state.current_page = "👤 User Login"
    time.sleep(0.5)
    st.rerun()


# ==============================================================================
# AUTHENTICATION PAGE RENDERERS
# ==============================================================================
def render_user_login_page():
    """Renders the Candidate and Recruiter User Login portal."""
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 14px; margin-bottom: 20px;'>
        <div style='font-size: 32px;'>👤</div>
        <div>
            <h2 style='margin: 0; color: #F8FAFC;'>Candidate & Recruiter Login</h2>
            <div style='color: #38BDF8; font-size: 13px; font-weight: 600;'>Sign in to your talent intelligence account</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.2], gap="large")

    with col_left:
        st.markdown(f"""
        <div class='auth-banner-side'>
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 18px;'>
                {get_logo_svg(size=40, show_glow=True, prefix='usr_log')}
                <div>
                    <div style='font-size: 18px; font-weight: 800; color: #F8FAFC;'>TalentIQ AI</div>
                    <div style='font-size: 11px; color: #38BDF8; font-weight: 700; text-transform: uppercase;'>User Portal</div>
                </div>
            </div>
            <h3 style='color: #F8FAFC; font-size: 20px; margin-bottom: 12px; line-height: 1.3;'>
                Next-Gen AI Resume Screening & Matching
            </h3>
            <p style='color: #94A3B8; font-size: 13px; line-height: 1.6;'>
                Access your personalized workspace to create ATS-optimized resumes, screen candidate pools, inspect explainable matching scores, and generate learning roadmaps.
            </p>
            <div style='margin-top: 20px;'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='color: #34D399;'>⚡</span>
                    <span style='color: #E2E8F0; font-size: 13px;'>Dense 384-D sentence transformer embeddings</span>
                </div>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='color: #38BDF8;'>📄</span>
                    <span style='color: #E2E8F0; font-size: 13px;'>Multi-template candidate resume builder</span>
                </div>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='color: #A78BFA;'>🛡️</span>
                    <span style='color: #E2E8F0; font-size: 13px;'>100% private, zero API-fee CPU inference</span>
                </div>
            </div>
            <div style='margin-top: 28px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 12px; color: #64748B;'>
                Are you a system administrator? Access the administrative console below.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🛡️ Switch to Admin Portal", type="secondary", use_container_width=True, key="switch_to_adm"):
            st.session_state.current_page = "🛡️ Admin Login"
            st.rerun()

    with col_right:
        st.markdown("### 🔑 Sign In to Your Account")
        with st.form("user_login_form"):
            user_email = st.text_input("Email Address:", placeholder="e.g. recruiter@resumerank.ai", key="usr_login_email")
            user_pass = st.text_input("Password:", type="password", placeholder="Enter your password", key="usr_login_pass")
            
            show_pwd = st.checkbox("Show password plaintext", key="usr_login_show_pwd")
            if show_pwd:
                st.caption(f"Password preview: `{user_pass}`")

            submit_login = st.form_submit_button("Sign In as User", type="primary", use_container_width=True)

            if submit_login:
                if not user_email or not user_pass:
                    st.error("Please enter both email address and password.")
                else:
                    succ, u_data, msg = authenticate_user(user_email, user_pass, required_role="user")
                    if succ and u_data:
                        u_data["is_authenticated"] = True
                        st.session_state.user = u_data
                        st.success(f"Welcome back, {u_data.get('full_name')}! Redirecting to Dashboard...")
                        time.sleep(0.4)
                        st.session_state.current_page = "📊 Dashboard"
                        st.rerun()
                    else:
                        st.error(msg)

        # Registration Option Link
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='display: flex; justify-content: space-between; align-items: center; background: rgba(30, 41, 59, 0.5); padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border-color);'>
            <span style='font-size: 13px; color: #94A3B8;'>Don't have an account yet?</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📝 Register New Account", use_container_width=True, type="secondary", key="usr_goto_reg"):
            st.session_state.current_page = "📝 User Registration"
            st.rerun()

        # Forgot Password Expander
        with st.expander("🔄 Forgot Password?"):
            st.caption("Generate a single-use password reset token:")
            reset_email_input = st.text_input("Registered Account Email:", key="fp_usr_email")
            if st.button("Request Reset Token", key="fp_usr_req_btn"):
                succ, msg, token = initiate_password_reset(reset_email_input)
                if succ:
                    st.success(msg)
                    if token:
                        st.info(f"Your single-use reset token: `{token}`")
                else:
                    st.error(msg)

            st.markdown("---")
            with st.form("fp_confirm_form"):
                token_val = st.text_input("Reset Token:", placeholder="rst_...", key="fp_tok_val")
                new_pwd_val = st.text_input("New Password:", type="password", key="fp_new_pwd")
                submit_fp = st.form_submit_button("Update Password", key="fp_confirm_submit")
                if submit_fp:
                    succ, msg = complete_password_reset(token_val, new_pwd_val)
                    if succ:
                        st.success(msg)
                    else:
                        st.error(msg)

        # Quick Demo Personas
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⚡ Quick Demo Evaluation Personas"):
            st.caption("Click any persona below to quickly authenticate for demo testing:")
            p1, p2, p3 = st.columns(3)
            with p1:
                if st.button("👤 Sarah Jenkins\n(Recruiter Lead)", use_container_width=True, key="demo_sarah"):
                    succ, u_data, _ = authenticate_user("recruiter@resumerank.ai", "Recruiter@2026", required_role="user")
                    if succ and u_data:
                        u_data["is_authenticated"] = True
                        st.session_state.user = u_data
                        st.success("Authenticated as Sarah Jenkins!")
                        time.sleep(0.3)
                        st.session_state.current_page = "📊 Dashboard"
                        st.rerun()
            with p2:
                if st.button("👤 David Chen\n(Hiring Manager)", use_container_width=True, key="demo_david"):
                    succ, u_data, _ = authenticate_user("manager@resumerank.ai", "Manager@2026", required_role="user")
                    if succ and u_data:
                        u_data["is_authenticated"] = True
                        st.session_state.user = u_data
                        st.success("Authenticated as David Chen!")
                        time.sleep(0.3)
                        st.session_state.current_page = "📊 Dashboard"
                        st.rerun()
            with p3:
                if st.button("👤 Demo Judge\n(Guest Evaluator)", use_container_width=True, key="demo_judge"):
                    succ, u_data, _ = authenticate_user("guest@resumerank.ai", "Guest@2026", required_role="user")
                    if succ and u_data:
                        u_data["is_authenticated"] = True
                        st.session_state.user = u_data
                        st.success("Authenticated as Guest Evaluator!")
                        time.sleep(0.3)
                        st.session_state.current_page = "📊 Dashboard"
                        st.rerun()


def render_user_registration_page():
    """Renders the User Registration page with password match validation."""
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 14px; margin-bottom: 20px;'>
        <div style='font-size: 32px;'>📝</div>
        <div>
            <h2 style='margin: 0; color: #F8FAFC;'>Create New User Account</h2>
            <div style='color: #38BDF8; font-size: 13px; font-weight: 600;'>Join TalentIQ AI for intelligent resume creation and screening</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_info, col_form = st.columns([1, 1.2], gap="large")

    with col_info:
        st.markdown(f"""
        <div class='auth-banner-side'>
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 18px;'>
                {get_logo_svg(size=40, show_glow=True, prefix='usr_reg')}
                <div>
                    <div style='font-size: 18px; font-weight: 800; color: #F8FAFC;'>TalentIQ AI</div>
                    <div style='font-size: 11px; color: #38BDF8; font-weight: 700; text-transform: uppercase;'>Candidate & Recruiter</div>
                </div>
            </div>
            <h3 style='color: #F8FAFC; font-size: 20px; margin-bottom: 12px; line-height: 1.3;'>
                Instant Account Provisioning
            </h3>
            <p style='color: #94A3B8; font-size: 13px; line-height: 1.6;'>
                Create your account to save custom resumes, benchmark your profile against real job specs, run instant AI matching, and export ATS audits.
            </p>
            <div style='margin-top: 20px;'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='color: #34D399;'>🔒</span>
                    <span style='color: #E2E8F0; font-size: 13px;'>Bcrypt cryptographic salted password protection</span>
                </div>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='color: #38BDF8;'>💾</span>
                    <span style='color: #E2E8F0; font-size: 13px;'>Persistent SQLite account storage</span>
                </div>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <span style='color: #A78BFA;'>👥</span>
                    <span style='color: #E2E8F0; font-size: 13px;'>Enforced candidate/recruiter user permissions</span>
                </div>
            </div>
            <div style='margin-top: 28px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 12px; color: #64748B;'>
                Already have an account? <a href='#' style='color: #38BDF8; font-weight: 700;'>Sign In</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔑 Already have an account? Sign In", type="secondary", use_container_width=True, key="reg_goto_login"):
            st.session_state.current_page = "👤 User Login"
            st.rerun()

    with col_form:
        st.markdown("### 📝 Account Registration Details")
        with st.form("user_registration_form"):
            reg_name = st.text_input("Full Name:", placeholder="e.g. Alex Rivera", key="reg_name_inp")
            reg_email = st.text_input("Email Address:", placeholder="e.g. alex.rivera@example.com", key="reg_email_inp")
            reg_role = st.selectbox(
                "Role / Persona:",
                ["Candidate / Job Seeker", "Recruiter / Talent Lead", "Hiring Manager", "Technical Interviewer"],
                key="reg_role_inp"
            )
            reg_pass = st.text_input(
                "Password (min 6 characters, 1 letter, 1 number):",
                type="password",
                key="reg_pass_inp"
            )
            reg_confirm_pass = st.text_input(
                "Confirm Password:",
                type="password",
                key="reg_confirm_pass_inp"
            )

            show_pwd = st.checkbox("Show passwords plaintext", key="reg_show_pwd")
            if show_pwd:
                st.caption(f"Password: `{reg_pass}` | Confirm: `{reg_confirm_pass}`")

            submit_reg = st.form_submit_button("Create User Account", type="primary", use_container_width=True)

            if submit_reg:
                if not reg_name or not reg_email or not reg_pass or not reg_confirm_pass:
                    st.error("All registration fields are required.")
                elif reg_pass != reg_confirm_pass:
                    st.error("Passwords do not match. Please verify both password entries.")
                else:
                    succ, u_data, msg = register_user(reg_email, reg_pass, reg_name, role=reg_role)
                    if succ and u_data:
                        u_data["is_authenticated"] = True
                        st.session_state.user = u_data
                        st.success(f"Account successfully created for {reg_name}! Redirecting to User Dashboard...")
                        time.sleep(0.5)
                        st.session_state.current_page = "📊 Dashboard"
                        st.rerun()
                    else:
                        st.error(msg)


def render_admin_login_page():
    """Renders the dedicated Admin Login portal with purple styling."""
    st.markdown("""
    <div class='admin-portal-header'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div style='display: flex; align-items: center; gap: 14px;'>
                <div style='font-size: 34px;'>🛡️</div>
                <div>
                    <h2 style='margin: 0; color: #FFFFFF; font-size: 24px; font-weight: 800;'>Administrator Command Gateway</h2>
                    <div style='color: #C084FC; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;'>
                        Restricted Access &middot; Platform Governance
                    </div>
                </div>
            </div>
            <span class='admin-badge' style='font-size: 12px; padding: 6px 14px;'>SECURE GATEWAY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_sec, col_form = st.columns([1, 1.2], gap="large")

    with col_sec:
        st.markdown(f"""
        <div class='admin-card' style='padding: 24px;'>
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 18px;'>
                {get_logo_svg(size=40, show_glow=True, prefix='adm_log')}
                <div>
                    <div style='font-size: 18px; font-weight: 800; color: #FFFFFF;'>TalentIQ Governance</div>
                    <div style='font-size: 11px; color: #C084FC; font-weight: 700; text-transform: uppercase;'>Admin Control Center</div>
                </div>
            </div>
            <h4 style='color: #F8FAFC; margin-bottom: 10px; font-size: 16px;'>Administrative Privileges</h4>
            <div style='font-size: 13px; color: #CBD5E1; line-height: 1.6;'>
                This gateway is strictly reserved for authorized platform administrators. Access grants full governance over:
            </div>
            <ul style='color: #CBD5E1; font-size: 13px; line-height: 1.8; margin-top: 10px; padding-left: 20px;'>
                <li><strong style='color: #FFFFFF;'>User Governance:</strong> Activate, suspend, and delete user accounts.</li>
                <li><strong style='color: #FFFFFF;'>Resume Database:</strong> Inspect candidate metadata, skills, and scores.</li>
                <li><strong style='color: #FFFFFF;'>Job Management:</strong> Create, edit, and delete system job requirements.</li>
                <li><strong style='color: #FFFFFF;'>Platform Telemetry:</strong> Audit screening logs and export CSV reports.</li>
            </ul>
            <div style='background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 10px; padding: 12px; margin-top: 18px;'>
                <div style='font-size: 11px; color: #C084FC; font-weight: 800; text-transform: uppercase;'>Default System Administrator:</div>
                <div style='font-size: 13px; color: #FFFFFF; font-weight: 700; margin-top: 2px;'>{DEFAULT_ADMIN_EMAIL}</div>
                <div style='font-size: 11px; color: #94A3B8; margin-top: 2px;'>Pre-provisioned in persistent SQLite database.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👤 Looking for Candidate / User Login? Switch to User Portal", type="secondary", use_container_width=True, key="adm_goto_usr"):
            st.session_state.current_page = "👤 User Login"
            st.rerun()

    with col_form:
        st.markdown("### 🛡️ Administrator Authentication")
        st.caption("Enter administrative credentials to access the governance console:")

        with st.form("admin_login_form"):
            admin_email = st.text_input(
                "Admin Email Address:",
                value="admin@airesume.com",
                placeholder="admin@airesume.com",
                key="adm_email_inp"
            )
            admin_pass = st.text_input(
                "Admin Password:",
                type="password",
                placeholder="Enter administrator password",
                key="adm_pass_inp"
            )

            show_pwd = st.checkbox("Show password plaintext", key="adm_show_pwd")
            if show_pwd:
                st.caption(f"Password preview: `{admin_pass}`")

            submit_admin = st.form_submit_button("🛡️ Sign In to Admin Command Center", type="primary", use_container_width=True)

            if submit_admin:
                if not admin_email or not admin_pass:
                    st.error("Both administrator email and password are required.")
                else:
                    succ, u_data, msg = authenticate_user(admin_email, admin_pass, required_role="admin")
                    if succ and u_data:
                        u_data["is_authenticated"] = True
                        st.session_state.user = u_data
                        st.success(f"Administrator verified: {u_data.get('full_name')}! Loading command center...")
                        time.sleep(0.4)
                        st.session_state.current_page = "🛡️ Admin Dashboard"
                        st.rerun()
                    else:
                        st.error(msg)

        # Quick Helper for Demo Evaluators
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("⚡ Evaluation Quick-Fill: Default Admin Credentials"):
            st.info(f"**Username:** `{DEFAULT_ADMIN_EMAIL}`\n\n**Password:** `{DEFAULT_ADMIN_PASSWORD}`")
            if st.button("🚀 Fast Sign In with Default Admin", use_container_width=True, type="secondary", key="adm_quick_login"):
                succ, u_data, msg = authenticate_user(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD, required_role="admin")
                if succ and u_data:
                    u_data["is_authenticated"] = True
                    st.session_state.user = u_data
                    st.success("Authenticated as Administrator!")
                    time.sleep(0.3)
                    st.session_state.current_page = "🛡️ Admin Dashboard"
                    st.rerun()
                else:
                    st.error(msg)


# ==============================================================================
# PAGE 1: 🏠 LANDING PAGE
# ==============================================================================
if st.session_state.current_page == "🏠 LANDING PAGE" or st.session_state.current_page == "🏠 Landing Page":
    # Top Navbar Component
    st.markdown(render_navbar_html(st.session_state.user), unsafe_allow_html=True)

    # Startup-Grade Hero Section
    st.markdown(f"""
    <div class='hero-container'>
        <div class='hero-badge'>
            ✨ Next-Gen AI Talent Intelligence Platform &middot; Production & Hackathon Ready
        </div>
        <div class='hero-title'>
            Find the Right Talent. <span class='brand-gradient-text'>Faster with AI.</span>
        </div>
        <div class='hero-subtitle'>
            AI Resume Screening and Job Matching System transforms hiring by combining dense 384-dimensional
            contextual sentence embeddings with evidence-grounded skill extraction. Rapidly screen, evaluate,
            and rank hundreds of candidates with mathematical explainability, zero API fees, and ethical fair-hiring safeguards.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main Call-to-Action Buttons
    cta_c1, cta_c2, cta_c3, cta_c4, cta_c5 = st.columns([1.1, 1.1, 1.2, 1.1, 1.1])
    with cta_c1:
        if st.button("👤 User Login", type="primary", use_container_width=True):
            st.session_state.current_page = "👤 User Login"
            st.rerun()
    with cta_c2:
        if st.button("🛡️ Admin Login", type="secondary", use_container_width=True):
            st.session_state.current_page = "🛡️ Admin Login"
            st.rerun()
    with cta_c3:
        if st.button("📝 User Registration", type="secondary", use_container_width=True):
            st.session_state.current_page = "📝 User Registration"
            st.rerun()
    with cta_c4:
        if st.button("📁 Explore Demo", type="secondary", use_container_width=True):
            with st.spinner("Loading demo candidate resumes and computing embeddings..."):
                succ = load_demo_data_action(model, semantic_wt, skill_wt, shortlist_cutoff)
                if succ:
                    st.session_state.current_page = "📊 Dashboard"
                    st.success("Loaded demo candidates! Redirecting to Dashboard...")
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error("Demo files not found. Please upload resumes manually in Resume Screening.")
    with cta_c5:
        if st.button("📝 Resume Builder", type="secondary", use_container_width=True):
            st.session_state.current_page = "📝 Resume Builder"
            st.rerun()

    # Dual Showcase Portal Cards (Candidate vs Admin)
    st.markdown("<br>", unsafe_allow_html=True)
    p_col1, p_col2 = st.columns(2, gap="large")
    with p_col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(30, 58, 138, 0.28), rgba(15, 23, 42, 0.7)); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 16px; padding: 22px; height: 100%; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);'>
            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;'>
                <div style='font-size: 26px;'>👤</div>
                <span class='badge-pill badge-matched' style='font-size: 11px;'>Candidate & Recruiter Portal</span>
            </div>
            <h3 style='color: #F8FAFC; margin: 0 0 10px 0; font-size: 19px;'>Candidate & Talent Experience</h3>
            <p style='color: #94A3B8; font-size: 13.5px; line-height: 1.6; margin-bottom: 16px;'>
                Empower your career or talent screening pipeline. Craft ATS-optimized resumes with 4 modern layouts, run dense 384-dimensional semantic matching against job specs, identify skill gaps with personalized upskilling roadmaps, and download compliance-ready reports.
            </p>
            <div style='font-size: 12px; color: #38BDF8; font-weight: 700; margin-bottom: 14px;'>
                ✓ Multi-format Resume Builder &middot; ✓ Semantic Scoring &middot; ✓ Skill Gap Roadmaps
            </div>
        </div>
        """, unsafe_allow_html=True)
        u_b1, u_b2 = st.columns(2)
        with u_b1:
            if st.button("👤 Sign In as User", key="lp_user_login", type="primary", use_container_width=True):
                st.session_state.current_page = "👤 User Login"
                st.rerun()
        with u_b2:
            if st.button("📝 Register Account", key="lp_user_reg", use_container_width=True):
                st.session_state.current_page = "📝 User Registration"
                st.rerun()

    with p_col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(88, 28, 135, 0.28), rgba(15, 23, 42, 0.7)); border: 1px solid rgba(168, 85, 247, 0.4); border-radius: 16px; padding: 22px; height: 100%; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);'>
            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;'>
                <div style='font-size: 26px;'>🛡️</div>
                <span class='admin-badge' style='font-size: 11px;'>Enterprise Governance</span>
            </div>
            <h3 style='color: #F8FAFC; margin: 0 0 10px 0; font-size: 19px;'>Administrator Command Center</h3>
            <p style='color: #94A3B8; font-size: 13.5px; line-height: 1.6; margin-bottom: 16px;'>
                Secure governance command center for platform administrators. Manage user lifecycles with instant activation/deactivation, govern candidate resume databases, configure target job taxonomies, inspect real-time screening telemetry, and export system audit logs.
            </p>
            <div style='font-size: 12px; color: #C084FC; font-weight: 700; margin-bottom: 14px;'>
                ✓ User Lifecycle Management &middot; ✓ SQLite Persistence &middot; ✓ Telemetry Audit Logs
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🛡️ Access Admin Portal", key="lp_admin_login", type="secondary", use_container_width=True):
            st.session_state.current_page = "🛡️ Admin Login"
            st.rerun()

    # Visual Representation of Resumes being matched to job requirements
    st.markdown(render_visual_matching_showcase(), unsafe_allow_html=True)

    # Live Metric Highlights Grid
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(render_stat_card_html("100%", "Local CPU Inference", "⚡", "Zero API Cost", "positive"), unsafe_allow_html=True)
    with m2:
        st.markdown(render_stat_card_html("384-D", "Dense Transformer Embeddings", "🧠", "Contextual", "positive"), unsafe_allow_html=True)
    with m3:
        st.markdown(render_stat_card_html("8+ Domains", "Curated Tech Taxonomy", "🎯", "Comprehensive", "positive"), unsafe_allow_html=True)
    with m4:
        st.markdown(render_stat_card_html("0%", "Hallucinated Credentials", "🛡️", "Strictly Grounded", "positive"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 5 High-Impact Feature Cards (User Spec)
    st.markdown("### 🌟 Intelligent Capabilities Built for High-Volume Talent Teams")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>📄</div>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>1. AI Resume Parsing</h4>
            <p style='color: #94A3B8; font-size: 13.5px; line-height: 1.6;'>
                High-speed extraction for multiple PDF and DOCX files using PyMuPDF and python-docx. Extracts structured contact facts, education spans, and candidate summaries without data loss.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with f_col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🧠</div>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>2. Semantic Job Matching</h4>
            <p style='color: #94A3B8; font-size: 13.5px; line-height: 1.6;'>
                Leverages deep transformer sentence embeddings to capture conceptual fit beyond brittle keyword matching. Detects that 'container orchestration' maps to 'Docker' and 'Kubernetes'.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with f_col3:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🏆</div>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>3. Candidate Ranking</h4>
            <p style='color: #94A3B8; font-size: 13.5px; line-height: 1.6;'>
                Calculates a transparent composite match score balancing contextual relevance and exact technical prerequisites with customizable recruiter weight sliders.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    f_col4, f_col5 = st.columns(2)
    with f_col4:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🗺️</div>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>4. Skill Gap Analysis</h4>
            <p style='color: #94A3B8; font-size: 13.5px; line-height: 1.6;'>
                Identifies missing technical requirements with visual distinction between matched, preferred, and absent competencies. Generates actionable upskilling roadmaps and mini-projects.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with f_col5:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🔍</div>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>5. Explainable AI (XAI)</h4>
            <p style='color: #94A3B8; font-size: 13.5px; line-height: 1.6;'>
                Eliminates the black box: quotes verbatim resume sentences proving candidate skills, provides mathematical score breakdowns, and strictly categorizes extracted facts versus model estimates.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3-Step Workflow Section
    st.markdown("### ⚡ Three-Step Autonomous Workflow")
    w1, w2, w3 = st.columns(3)
    with w1:
        st.markdown("""
        <div class='step-card'>
            <span class='step-num-badge' style='background: rgba(56, 189, 248, 0.15); color: #38BDF8;'>STEP 01</span>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>Upload Resumes</h4>
            <p style='color: #94A3B8; font-size: 13px; line-height: 1.5;'>
                Ingest PDF and DOCX candidate resumes simultaneously with drag-and-drop. Automatic validation, text normalization, and local parsing.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with w2:
        st.markdown("""
        <div class='step-card'>
            <span class='step-num-badge' style='background: rgba(129, 140, 248, 0.15); color: #818CF8;'>STEP 02</span>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>Add Job Description</h4>
            <p style='color: #94A3B8; font-size: 13px; line-height: 1.5;'>
                Paste role criteria or select from engineering presets. AI extracts required vs preferred skills, experience benchmarks, and role clarity scores.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with w3:
        st.markdown("""
        <div class='step-card'>
            <span class='step-num-badge' style='background: rgba(192, 132, 252, 0.15); color: #C084FC;'>STEP 03</span>
            <h4 style='margin: 0 0 8px 0; color: #F8FAFC;'>Discover Best Matches</h4>
            <p style='color: #94A3B8; font-size: 13px; line-height: 1.5;'>
                Explore the interactive leaderboard, review candidate quotes, inspect skill gaps, compare finalists head-to-head, and export sanitized CSV reports.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Ethical AI Banner
    st.markdown(f"""
    <div class='ethics-card'>
        <div style='font-size: 26px;'>⚖️</div>
        <div>
            <div style='font-weight: 800; color: #E0E7FF; font-size: 14px; letter-spacing: 0.2px;'>
                Ethical AI, Bias Mitigation & Candidate Privacy Framework
            </div>
            <div style='font-size: 12.5px; color: #CBD5E1; line-height: 1.55; margin-top: 4px;'>
                {ETHICAL_DISCLAIMER}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Polished Footer
    st.markdown(render_footer_html(), unsafe_allow_html=True)


# ==============================================================================
# PAGE 2: 📊 RECRUITER DASHBOARD
# ==============================================================================
elif st.session_state.current_page == "📊 Dashboard":
    st.markdown("## 📊 Recruiter Analytics & Executive Dashboard")
    st.caption("Strategic talent pipeline overview, score distributions, and real-time screening telemetry.")

    ranked = st.session_state.ranked_results

    # Data Source Notice Badge
    if ranked:
        if st.session_state.is_demo_data:
            st.info("ℹ️ **Data Source: Demo Candidate Cohort**. Displaying pre-analyzed test profiles for hackathon presentation. Upload custom resumes in **Resume Screening** to process live candidates.")
        else:
            st.success("🟢 **Data Source: Active User Session**. Displaying metrics calculated directly from your uploaded resumes.")
    else:
        st.warning("⚠️ **No Active Screening Data**. Please upload resumes in **Resume Screening** or click below to populate the dashboard with instant demo candidates.")
        if st.button("🚀 Populate Dashboard with Demo Candidates", type="primary"):
            with st.spinner("Loading demo candidate resumes..."):
                load_demo_data_action(model, semantic_wt, skill_wt, shortlist_cutoff)
                st.rerun()

    if ranked:
        valid_candidates = [c for c in ranked if c.get("status") == "Processed"]
        total_cand = len(ranked)
        shortlisted = [c for c in valid_candidates if c.get("is_shortlisted")]
        shortlisted_cnt = len(shortlisted)
        avg_score = (sum(c["composite_score"] for c in valid_candidates) / len(valid_candidates)) if valid_candidates else 0.0
        avg_semantic = (sum(c["semantic_score_pct"] for c in valid_candidates) / len(valid_candidates)) if valid_candidates else 0.0
        avg_skill = (sum(c["skill_match_pct"] for c in valid_candidates) / len(valid_candidates)) if valid_candidates else 0.0
        top_cand = valid_candidates[0] if valid_candidates else None

        # 4 Key Stat Cards (User Spec)
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.markdown(render_stat_card_html(str(total_cand), "Resumes Analyzed", "📄", "Active Pool", "positive"), unsafe_allow_html=True)
        with d2:
            st.markdown(render_stat_card_html("1 Active", "Jobs Processed", "🎯", st.session_state.selected_preset[:16], "positive"), unsafe_allow_html=True)
        with d3:
            st.markdown(render_stat_card_html(f"{shortlisted_cnt} ({shortlisted_cnt/max(total_cand,1)*100:.0f}%)", f"Shortlisted (≥{shortlist_cutoff:.0f}%)", "✅", "Top Tier", "positive"), unsafe_allow_html=True)
        with d4:
            st.markdown(render_stat_card_html(f"{avg_score:.1f}%", "Average Match Score", "📈", f"Sem: {avg_semantic:.0f}%", "positive"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Leaderboard Snippet & Recent Activity Stream
        col_lead, col_act = st.columns([1.5, 1], gap="large")

        with col_lead:
            st.markdown("#### 🏆 Top Matching Candidates")
            st.caption("Highest-scoring candidates against current job specification:")
            for idx, c in enumerate(valid_candidates[:3]):
                podium_class = "cand-rank-gold" if idx == 0 else ("cand-rank-silver" if idx == 1 else "cand-rank-bronze")
                badge_bg = "#10B981" if c.get("is_shortlisted") else "#F59E0B"
                badge_txt = "SHORTLISTED" if c.get("is_shortlisted") else "UNDER REVIEW"
                
                st.markdown(f"""
                <div style='background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 14px; padding: 14px 18px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;'>
                    <div style='display: flex; align-items: center;'>
                        <span class='cand-rank {podium_class}'>#{c['rank']}</span>
                        <div>
                            <div style='font-weight: 700; font-size: 15px; color: #F8FAFC;'>{c['candidate_name']}</div>
                            <div style='font-size: 12px; color: #94A3B8;'>{c['metadata'].get('email') or 'No email'} &middot; Sem: {c['semantic_score_pct']}% &middot; Skills: {c['skill_match_pct']}%</div>
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 20px; font-weight: 800; color: #38BDF8;'>{c['composite_score']}%</div>
                        <span style='background: {badge_bg}; color: #fff; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 10px;'>
                            {badge_txt}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("👉 View Full Candidate Rankings & Deep Dive", type="secondary", use_container_width=True):
                st.session_state.current_page = "🏆 Candidate Rankings"
                st.rerun()

        with col_act:
            st.markdown("#### ⚡ Recent Activity & Audit Stream")
            st.caption("Live event log for talent screening sessions:")
            st.markdown("<div class='activity-stream'>", unsafe_allow_html=True)
            for item in st.session_state.recent_activity[:4]:
                st.markdown(f"""
                <div class='activity-item'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-weight: 700; font-size: 13px; color: #F8FAFC;'>{item['title']}</span>
                        <span style='font-size: 10px; color: #94A3B8;'>{item['time']}</span>
                    </div>
                    <div style='font-size: 12px; color: #94A3B8; margin-top: 2px;'>{item['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Visual Analytics Charts
        st.markdown("### 📈 Talent Analytics & Match Distributions")
        c_left, c_right = st.columns([1, 1], gap="large")
        with c_left:
            st.markdown("##### Composite Match vs Semantic vs Skill Overlap (%)")
            chart_data = pd.DataFrame({
                "Candidate": [c["candidate_name"] for c in valid_candidates],
                "Composite Score (%)": [c["composite_score"] for c in valid_candidates],
                "Semantic Sim (%)": [c["semantic_score_pct"] for c in valid_candidates],
                "Skill Match (%)": [c["skill_match_pct"] for c in valid_candidates]
            }).set_index("Candidate")
            st.bar_chart(chart_data)

        with c_right:
            st.markdown("##### Candidate Skill Counts (Matched vs Missing)")
            skill_chart_data = pd.DataFrame({
                "Candidate": [c["candidate_name"] for c in valid_candidates],
                "Matched Skills": [len(c.get("matched_skills", [])) for c in valid_candidates],
                "Missing Skills": [len(c.get("missing_skills", [])) for c in valid_candidates],
                "Bonus Skills": [len(c.get("additional_skills", [])) for c in valid_candidates]
            }).set_index("Candidate")
            st.bar_chart(skill_chart_data)

        # Quick Actions Row
        st.markdown("---")
        st.markdown("#### ⚡ Quick Actions")
        qa1, qa2, qa3, qa4, qa5 = st.columns(5)
        with qa1:
            if st.button("⚡ Run New Screening", use_container_width=True):
                st.session_state.current_page = "⚡ Resume Screening"
                st.rerun()
        with qa2:
            if st.button("📝 Build Resume", use_container_width=True):
                st.session_state.current_page = "📝 Resume Builder"
                st.rerun()
        with qa3:
            if st.button("⚖️ Compare Finalists", use_container_width=True):
                st.session_state.current_page = "⚖️ Candidate Comparison"
                st.rerun()
        with qa4:
            if st.button("🗺️ Analyze Skill Gaps", use_container_width=True):
                st.session_state.current_page = "🗺️ Skill Gap Analysis"
                st.rerun()
        with qa5:
            csv_data = generate_csv_report(ranked, jd_title=st.session_state.selected_preset)
            st.download_button(
                label="📥 Export Report (CSV)",
                data=csv_data,
                file_name="resumescreening_executive_report.csv",
                mime="text/csv",
                use_container_width=True
            )


# ==============================================================================
# PAGE: 📝 RESUME BUILDER
# ==============================================================================
elif st.session_state.current_page == "📝 Resume Builder" or st.session_state.current_page == "Resume Builder":
    render_resume_builder_page(cached_model=model)


# ==============================================================================
# PAGE 3: ⚡ RESUME SCREENING & JOB MATCHING
# ==============================================================================
elif st.session_state.current_page == "⚡ Resume Screening":
    st.markdown("## ⚡ Resume Screening & Job Matching Studio")
    st.caption("Upload multiple candidate resumes, configure job description requirements, and run semantic matching.")

    col_jd, col_res = st.columns([1, 1], gap="large")

    # Left: Job Description Panel
    with col_jd:
        st.markdown("### 1. Job Description & Criteria")
        preset_choices = ["Select role preset or customize..."] + list(SAMPLE_JOB_DESCRIPTIONS.keys())
        selected_preset = st.selectbox(
            "Target Engineering Role Preset:",
            options=preset_choices,
            index=1 if st.session_state.selected_preset == "AI / Machine Learning Engineer" else 0
        )

        if selected_preset != "Select role preset or customize..." and selected_preset != st.session_state.selected_preset:
            st.session_state.selected_preset = selected_preset
            st.session_state.jd_text_input = SAMPLE_JOB_DESCRIPTIONS[selected_preset]
            st.rerun()

        jd_text = st.text_area(
            "Job Description Text:",
            value=st.session_state.jd_text_input,
            height=280,
            placeholder="Paste complete job description, technical requirements, responsibilities, and qualifications..."
        )
        st.session_state.jd_text_input = jd_text

        # Quick JD words counter & audit snippet
        word_count = len(jd_text.strip().split())
        st.caption(f"📝 Word Count: **{word_count} words** &middot; Minimum recommended: 30 words")

        # Quick Inline Review of Extracted Requirements
        if word_count >= 20:
            with st.expander("🔎 Quick Preview: Extracted Role Requirements", expanded=False):
                quick_analysis = analyze_job_description(jd_text)
                st.markdown("**Mandatory Skills Identified:**")
                st.markdown(render_skill_badges(quick_analysis["required_skills"], "matched"), unsafe_allow_html=True)
                if quick_analysis["preferred_skills"]:
                    st.markdown("**Preferred Skills Identified:**")
                    st.markdown(render_skill_badges(quick_analysis["preferred_skills"], "bonus"), unsafe_allow_html=True)
                st.caption(f"Target Exp: {quick_analysis['experience_required']} &middot; Clarity Score: {quick_analysis['clarity_score']}%")

    # Right: Resume Upload Panel
    with col_res:
        st.markdown("### 2. Candidate Resumes")
        uploaded_files = st.file_uploader(
            "Upload Resumes (PDF or DOCX):",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Select one or multiple resumes in PDF or DOCX format. Files are parsed 100% locally on your machine."
        )

        if uploaded_files:
            is_valid, validation_errors = validate_uploaded_files(uploaded_files)
            if is_valid:
                st.success(f"📁 **{len(uploaded_files)} file(s) staged** for screening analysis.")
                # Show file breakdown list
                for f in uploaded_files:
                    f_size_kb = len(f.getvalue()) / 1024.0
                    st.markdown(f"""
                    <div style='background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 6px 12px; margin-bottom: 6px; display: flex; justify-content: space-between; font-size: 12px;'>
                        <span style='color: #F8FAFC;'>📄 {f.name}</span>
                        <span style='color: #94A3B8;'>{f_size_kb:.1f} KB &middot; <strong style='color:#34D399;'>Ready</strong></span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                for err in validation_errors:
                    st.error(err)
        elif st.session_state.parsed_resumes:
            st.info(f"📁 **{len(st.session_state.parsed_resumes)} resume(s)** currently in memory.")
            for r in st.session_state.parsed_resumes[:4]:
                st.markdown(f"""
                <div style='background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 6px 12px; margin-bottom: 6px; display: flex; justify-content: space-between; font-size: 12px;'>
                    <span style='color: #F8FAFC;'>📄 {r.get('filename')}</span>
                    <span style='color: #94A3B8;'>Words: {r.get('metadata', {}).get('word_count', 0)} &middot; <strong style='color:#60A5FA;'>Cached</strong></span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background: rgba(59, 130, 246, 0.05); border: 2px dashed rgba(59, 130, 246, 0.3); border-radius: 14px; padding: 26px; text-align: center;'>
                <div style='font-size: 32px; margin-bottom: 8px;'>📄</div>
                <div style='font-weight: 700; color: #F8FAFC; font-size: 15px;'>Drag & Drop Candidate Resumes</div>
                <div style='color: #94A3B8; font-size: 12px; margin-top: 4px;'>
                    Supports multiple PDF and DOCX documents simultaneously with local text extraction.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📁 Load Sample Test Resumes", use_container_width=True):
            with st.spinner("Loading sample resumes from disk..."):
                loaded = []
                if os.path.exists(sample_resumes_dir):
                    for fname in sorted(os.listdir(sample_resumes_dir)):
                        if fname.endswith((".pdf", ".docx")):
                            fpath = os.path.join(sample_resumes_dir, fname)
                            parsed = parse_resume(fpath, filename=fname)
                            loaded.append(parsed)
                if loaded:
                    st.session_state.parsed_resumes = loaded
                    st.session_state.is_demo_data = True
                    st.success(f"Loaded {len(loaded)} sample candidate resumes from `sample_data/resumes/`!")
                    time.sleep(0.3)
                    st.rerun()

    # Screening Run Trigger Section
    st.markdown("---")
    r_col1, r_col2 = st.columns([1.8, 1.2])
    with r_col1:
        st.markdown(f"""
        **Active Configuration**:
        Semantic Weight: `{semantic_wt * 100:.0f}%` &middot; Skill Weight: `{skill_wt * 100:.0f}%` &middot; Shortlist Cutoff: `{shortlist_cutoff:.0f}%`
        """)
    with r_col2:
        run_screening = st.button("🚀 Analyze and Match Candidates", type="primary", use_container_width=True)

    if run_screening:
        is_valid_jd, jd_msg = validate_job_description(jd_text)
        if not is_valid_jd:
            st.error(jd_msg)
        elif not uploaded_files and not st.session_state.parsed_resumes:
            st.error("Please upload at least one PDF or DOCX resume, or click 'Load Sample Test Resumes'.")
        else:
            p_bar = st.progress(0, text="Initializing parsing engine...")

            # 1. Parse resumes
            parsed_list = []
            if uploaded_files:
                for idx, uf in enumerate(uploaded_files):
                    p_bar.progress(int((idx / len(uploaded_files)) * 30), text=f"Parsing {uf.name}...")
                    parsed = parse_resume(uf, filename=uf.name)
                    parsed_list.append(parsed)
                st.session_state.is_demo_data = False
            else:
                parsed_list = st.session_state.parsed_resumes
                st.session_state.is_demo_data = True

            # 2. Semantic embeddings
            p_bar.progress(55, text="Computing dense sentence embeddings with Sentence-Transformers...")
            raw_sims = batch_compute_similarity(parsed_list, jd_text, model=model)

            # 3. Composite ranking & XAI
            p_bar.progress(85, text="Extracting skill evidence, analyzing gaps, and computing transparent rankings...")
            ranked_all, df_summary = rank_resumes(
                parsed_resumes=parsed_list,
                jd_text=jd_text,
                semantic_similarities=raw_sims,
                semantic_weight=semantic_wt,
                skill_weight=skill_wt,
                shortlist_threshold=shortlist_cutoff
            )

            p_bar.progress(100, text="Screening successfully completed!")
            st.session_state.ranked_results = ranked_all
            st.session_state.summary_df = df_summary
            st.session_state.parsed_resumes = parsed_list

            # Sync resumes and screening records to SQLite database
            try:
                curr_uid = st.session_state.user.get("id") if (st.session_state.user and st.session_state.user.get("id")) else "active_session_user"
                for p in parsed_list:
                    db_add_resume_record(
                        user_id=curr_uid,
                        filename=p.get("filename", "resume.pdf"),
                        file_type=p.get("file_type", "pdf"),
                        word_count=p.get("metadata", {}).get("word_count", 0),
                        extracted_email=p.get("metadata", {}).get("email", ""),
                        candidate_name=p.get("candidate_name", ""),
                        skills_detected=p.get("skills", []),
                        status="parsed"
                    )
                for item in ranked_all:
                    db_add_screening_record(
                        user_id=curr_uid,
                        job_title=st.session_state.selected_preset or "Target Job",
                        candidate_name=item.get("candidate_name", "Unknown"),
                        filename=item.get("filename", ""),
                        composite_score=float(item.get("composite_score", 0)),
                        semantic_score=float(item.get("semantic_score", 0)),
                        skill_score=float(item.get("skill_score", 0)),
                        decision="SHORTLISTED" if item.get("is_shortlisted") else "REVIEW"
                    )
            except Exception:
                pass

            # Log to activity stream
            st.session_state.recent_activity.insert(0, {
                "time": "Just now",
                "title": f"Screened {len(parsed_list)} Resumes",
                "desc": f"Top Candidate: {ranked_all[0]['candidate_name']} ({ranked_all[0]['composite_score']}%)",
                "tag": "SUCCESS",
                "color": "#10B981"
            })

            time.sleep(0.4)
            p_bar.empty()
            st.success("Analysis complete! Navigating to Candidate Rankings...")
            st.session_state.current_page = "🏆 Candidate Rankings"
            st.rerun()


# ==============================================================================
# PAGE 4: 🎯 JOB MATCHING (JOB DESCRIPTION INTELLIGENCE)
# ==============================================================================
elif st.session_state.current_page == "🎯 Job Matching":
    st.markdown("## 🎯 Job Description Intelligence & Pre-Screening Review")
    st.caption("AI-powered decomposition of job descriptions into Required vs Preferred criteria, experience requirements, and clarity score.")

    jd_analysis = analyze_job_description(st.session_state.jd_text_input)

    # Top Metrics Row
    jc1, jc2, jc3, jc4 = st.columns(4)
    with jc1:
        st.markdown(render_stat_card_html(str(len(jd_analysis['required_skills'])), "Required Skills", "✅", "Mandatory", "positive"), unsafe_allow_html=True)
    with jc2:
        st.markdown(render_stat_card_html(str(len(jd_analysis['preferred_skills'])), "Preferred Skills", "🌟", "Bonus Criteria", "positive"), unsafe_allow_html=True)
    with jc3:
        clarity_c = "#34D399" if jd_analysis['clarity_score'] >= 80 else "#FBBF24"
        st.markdown(render_stat_card_html(f"{jd_analysis['clarity_score']}%", "Role Clarity Score", "🔍", "Audit", "positive"), unsafe_allow_html=True)
    with jc4:
        st.markdown(render_stat_card_html(jd_analysis['experience_required'], "Target Experience", "⏳", "Prerequisite", "positive"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Decomposed Skills Breakdown
    col_req, col_pref = st.columns(2, gap="large")
    with col_req:
        st.markdown("#### ✅ Mandatory / Required Skills")
        st.caption("Identified core prerequisites that heavily determine technical qualification:")
        st.markdown(render_skill_badges(jd_analysis['required_skills'], "matched"), unsafe_allow_html=True)

    with col_pref:
        st.markdown("#### 🌟 Nice-to-Have / Preferred Skills")
        st.caption("Identified secondary competencies that award bonus alignment score:")
        st.markdown(render_skill_badges(jd_analysis['preferred_skills'], "bonus"), unsafe_allow_html=True)

    st.markdown("---")

    # Education & Clarity Audit
    col_edu, col_audit = st.columns(2, gap="large")
    with col_edu:
        st.markdown("#### 🎓 Education & Degree Expectations")
        st.info(f"**Prerequisites Detected**: {jd_analysis['education_required']}")

        st.markdown("#### 💪 Role Strengths")
        if jd_analysis["strengths"]:
            for s in jd_analysis["strengths"]:
                st.markdown(f"- ✅ {s}")
        else:
            st.markdown("*Standard specification.*")

    with col_audit:
        st.markdown("#### ⚠️ Ambiguity & Clarity Warnings")
        if jd_analysis["clarity_warnings"]:
            for w in jd_analysis["clarity_warnings"]:
                st.warning(f"⚠️ {w}")
        else:
            st.success("No ambiguity warnings detected! Job specification is precise and transparent.")

        if jd_analysis["buzzwords_found"]:
            st.markdown("##### 🚩 Buzzwords / Clichés Flagged:")
            for b in jd_analysis["buzzwords_found"]:
                st.error(f"'{b['term']}': {b['warning']}")


# ==============================================================================
# PAGE 5: 🏆 CANDIDATE RANKINGS (LEADERBOARD & XAI)
# ==============================================================================
elif st.session_state.current_page == "🏆 Candidate Rankings":
    st.markdown("## 🏆 Candidate Leaderboard & Explainable AI")
    st.caption("Contextual candidate rankings with formula transparency, grounded evidence quotes, and diagnostic feedback.")

    ranked = st.session_state.ranked_results
    if not ranked:
        st.warning("No screening results available yet. Please run screening from **Resume Screening** or load demo data.")
        if st.button("🚀 Load Instant Demo Candidates", type="primary"):
            with st.spinner("Loading demo candidate resumes..."):
                load_demo_data_action(model, semantic_wt, skill_wt, shortlist_cutoff)
                st.rerun()
    else:
        valid_candidates = [c for c in ranked if c.get("status") == "Processed"]

        # Multi-Faceted Filters & Search Bar
        st.markdown("#### 🔍 Smart Search & Multi-Faceted Filtering")
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            search_query = st.text_input("Search candidate or skill:", placeholder="Type candidate name or keyword...")
        with f2:
            min_score_filter = st.slider("Min Match Score (%)", 0, 100, 0, 5)
        with f3:
            sort_by = st.selectbox("Sort By:", ["Composite Match (High to Low)", "Semantic Sim (High to Low)", "Skill Match (High to Low)", "Candidate Name (A-Z)"])
        with f4:
            shortlist_only = st.checkbox("Shortlisted Only", value=False)

        # Filter Data
        filtered = valid_candidates.copy()
        if search_query:
            q = search_query.lower()
            filtered = [c for c in filtered if q in c["candidate_name"].lower() or any(q in s.lower() for s in c.get("matched_skills", []))]
        if min_score_filter > 0:
            filtered = [c for c in filtered if c["composite_score"] >= min_score_filter]
        if shortlist_only:
            filtered = [c for c in filtered if c.get("is_shortlisted")]

        if "Semantic" in sort_by:
            filtered.sort(key=lambda x: x["semantic_score_pct"], reverse=True)
        elif "Skill Match" in sort_by:
            filtered.sort(key=lambda x: x["skill_match_pct"], reverse=True)
        elif "Candidate Name" in sort_by:
            filtered.sort(key=lambda x: x["candidate_name"].lower())
        else:
            filtered.sort(key=lambda x: x["composite_score"], reverse=True)

        st.caption(f"Showing **{len(filtered)} of {len(valid_candidates)}** candidates matching active filters.")

        # Candidate Display Table
        table_rows = []
        for c in filtered:
            table_rows.append({
                "Rank": f"#{c['rank']}",
                "Candidate Name": c["candidate_name"],
                "Composite Match (%)": f"{c['composite_score']:.1f}%",
                "Semantic Sim (%)": f"{c['semantic_score_pct']:.1f}%",
                "Skill Match (%)": f"{c['skill_match_pct']:.1f}%",
                "Matched Skills": ", ".join(c.get("matched_skills", [])[:4]),
                "Missing Skills": ", ".join(c.get("missing_skills", [])[:3]),
                "Decision": "🟢 SHORTLISTED" if c.get("is_shortlisted") else "🟡 UNDER REVIEW"
            })
        if table_rows:
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Deep Dive Profile View
        st.markdown("### 🔬 Candidate Deep Dive & Grounded Evidence")
        cand_options = [c["candidate_name"] for c in filtered] if filtered else [c["candidate_name"] for c in valid_candidates]
        if cand_options:
            selected_cand_name = st.selectbox("Select Candidate for Deep Dive:", cand_options)
            cand = next((c for c in valid_candidates if c["candidate_name"] == selected_cand_name), valid_candidates[0])

            status_badge_color = "#10B981" if cand.get("is_shortlisted") else "#F59E0B"
            status_badge_text = "SHORTLISTED" if cand.get("is_shortlisted") else "UNDER REVIEW"

            # Profile Facts Extraction
            raw_text = cand.get("raw_text") or cand.get("clean_text") or ""
            profile_facts = extract_candidate_profile_facts(raw_text)

            podium_cls = "cand-rank-gold" if cand['rank'] == 1 else ("cand-rank-silver" if cand['rank'] == 2 else "cand-rank-bronze")

            st.markdown(f"""
            <div class='glass-card'>
                <div class='cand-header-box'>
                    <div>
                        <div style='display:flex; align-items:center;'>
                            <span class='cand-rank {podium_cls}'>#{cand['rank']}</span>
                            <span class='cand-name'>{cand['candidate_name']}</span>
                        </div>
                        <div style='font-size: 13px; color: #94A3B8; margin-top: 6px;'>
                            Email: {cand['metadata'].get('email') or 'Not Detected'} &middot; Word Count: {cand['metadata'].get('word_count', 0)} &middot; Est. Experience: {profile_facts.get('years_of_experience_est', 'Not stated')} yrs
                        </div>
                    </div>
                    <div>
                        <span style='background: {status_badge_color}; color: #ffffff; font-weight: 800; font-size: 12px; padding: 6px 14px; border-radius: 20px;'>
                            {status_badge_text}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Score Columns
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Composite Match Score", f"{cand['composite_score']}%")
                st.progress(cand['composite_score'] / 100.0)
            with s2:
                st.metric("Contextual Semantic Sim", f"{cand['semantic_score_pct']}%")
                st.progress(cand['semantic_score_pct'] / 100.0)
            with s3:
                st.metric("Technical Skill Overlap", f"{cand['skill_match_pct']}%")
                st.progress(cand['skill_match_pct'] / 100.0)

            # Mathematical Formula Card
            bdown = cand["explanation"]["score_breakdown"]
            st.markdown(f"""
            <div class='math-formula-box'>
                <strong>📐 Transparent Score Calculation:</strong><br>
                Final Score = {bdown['formula']}<br>
                <span style='color: #94A3B8; font-size: 12px;'>
                    Semantic Contribution: {bdown['semantic_contribution']}% (Weight: {bdown['semantic_weight_pct']}%) &middot; 
                    Skill Contribution: {bdown['skill_contribution']}% (Weight: {bdown['skill_weight_pct']}%)
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Extracted Facts vs AI Inferences Comparison
            st.markdown("#### ⚖️ Grounded Extracted Facts vs AI Model Inferences")
            categorized_elements = categorize_explanation_elements(cand["explanation"], profile_facts)
            col_facts, col_inf = st.columns(2, gap="large")
            with col_facts:
                st.markdown("**🟢 Extracted Facts (Directly from Resume Text)**")
                for f_item in categorized_elements["extracted_facts"]:
                    st.markdown(f"""
                    <div style='background: rgba(16, 185, 129, 0.08); border-left: 3px solid #10B981; padding: 8px 12px; margin-bottom: 8px; border-radius: 6px;'>
                        <span class='fact-tag tag-grounded-fact'>{f_item['type']}</span>
                        <div style='font-size: 13px; color: #E2E8F0; margin-top: 4px;'>{f_item['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_inf:
                st.markdown("**🟣 AI Model Inferences (Decision Support Estimates)**")
                for i_item in categorized_elements["model_inferences"]:
                    st.markdown(f"""
                    <div style='background: rgba(139, 92, 246, 0.08); border-left: 3px solid #8B5CF6; padding: 8px 12px; margin-bottom: 8px; border-radius: 6px;'>
                        <span class='fact-tag tag-model-inference'>{i_item['type']}</span>
                        <div style='font-size: 13px; color: #E2E8F0; margin-top: 4px;'>{i_item['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

            # Skills Breakdown Badges
            sk1, sk2, sk3 = st.columns(3)
            with sk1:
                st.markdown(f"##### ✅ Matched Skills ({len(cand['matched_skills'])})")
                st.markdown(render_skill_badges(cand['matched_skills'], "matched"), unsafe_allow_html=True)
            with sk2:
                st.markdown(f"##### ❌ Missing Job Skills ({len(cand['missing_skills'])})")
                st.markdown(render_skill_badges(cand['missing_skills'], "missing"), unsafe_allow_html=True)
            with sk3:
                st.markdown(f"##### 🌟 Bonus Skills ({len(cand['additional_skills'])})")
                st.markdown(render_skill_badges(cand['additional_skills'], "bonus"), unsafe_allow_html=True)

            # Verified Verbatim Evidence Snippets
            if cand.get("matched_evidence"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 🔎 Grounded Resume Evidence (Verbatim Excerpts)")
                st.caption("Verbatim passages extracted directly from candidate resume evidencing required qualifications:")
                for skill_name, snippet in cand["matched_evidence"].items():
                    st.markdown(f"""
                    <div style='background: rgba(15, 23, 42, 0.5); border-left: 3px solid #38BDF8; padding: 10px 14px; margin-bottom: 8px; border-radius: 6px; font-size: 13px;'>
                        <strong style='color:#38BDF8;'>{skill_name}</strong>: &ldquo;{snippet}&rdquo;
                    </div>
                    """, unsafe_allow_html=True)

            # Actionable Suggestions
            if cand["explanation"].get("actionable_suggestions"):
                st.markdown("---")
                st.markdown("#### 💡 Actionable Improvement Suggestions")
                for tip in cand["explanation"]["actionable_suggestions"]:
                    st.info(f"💡 {tip}")


# ==============================================================================
# PAGE 6: 🗺️ SKILL GAP ANALYSIS
# ==============================================================================
elif st.session_state.current_page == "🗺️ Skill Gap Analysis":
    st.markdown("## 🗺️ Skill Gap Analyzer & Upskilling Studio")
    st.caption("Visual indicators for matched vs missing competencies and personalized, project-based upskilling roadmaps.")

    ranked = st.session_state.ranked_results
    if not ranked:
        st.warning("Please run a screening analysis first to analyze skill gaps.")
    else:
        valid_candidates = [c for c in ranked if c.get("status") == "Processed"]
        cand_names = [c["candidate_name"] for c in valid_candidates]
        selected_cand = st.selectbox("Select Candidate for Skill Gap Roadmap:", cand_names)
        cand = next(c for c in valid_candidates if c["candidate_name"] == selected_cand)

        # Overview Gauges
        sg1, sg2, sg3 = st.columns(3)
        with sg1:
            st.metric("Skill Match Coverage", f"{cand['skill_match_pct']}%")
            st.progress(cand['skill_match_pct'] / 100.0)
        with sg2:
            st.metric("Matched Competencies", len(cand['matched_skills']))
        with sg3:
            st.metric("Missing Requirements", len(cand['missing_skills']))

        st.markdown("<br>", unsafe_allow_html=True)

        col_m, col_g = st.columns(2, gap="large")
        with col_m:
            st.markdown(f"#### ✅ Matched Competencies ({len(cand['matched_skills'])})")
            st.markdown(render_skill_badges(cand['matched_skills'], "matched"), unsafe_allow_html=True)
            if cand.get("additional_skills"):
                st.markdown(f"##### 🌟 Bonus / Additional Skills ({len(cand['additional_skills'])})")
                st.markdown(render_skill_badges(cand['additional_skills'], "bonus"), unsafe_allow_html=True)

        with col_g:
            st.markdown(f"#### ⚠️ Missing Requirements ({len(cand['missing_skills'])})")
            st.markdown(render_skill_badges(cand['missing_skills'], "missing"), unsafe_allow_html=True)

        missing_skills = cand.get("missing_skills", [])
        if not missing_skills:
            st.success(f"🎉 **100% Skill Coverage!** {cand['candidate_name']} matches all detected skills in the job specification!")
        else:
            st.markdown("---")
            st.markdown("### 📚 Personalized Upskilling Roadmap")
            st.caption("AI-curated learning topics, duration, core concepts, and hands-on project blueprints:")
            recommendations = get_recommendations_for_missing_skills(missing_skills)

            for rec in recommendations:
                st.markdown(f"""
                <div class='roadmap-step'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                        <h4 style='margin:0; color:#38BDF8;'>🚀 {rec['title']}</h4>
                        <span style='background:rgba(59, 130, 246, 0.15); color:#60A5FA; font-weight:700; font-size:11px; padding:3px 10px; border-radius:12px;'>
                            {rec.get('estimated_time', '2-4 weeks')}
                        </span>
                    </div>
                    <div style='font-size:13px; color:#E2E8F0; margin-bottom:8px;'>
                        <strong>Key Concepts to Master:</strong>
                        <ul style='margin: 4px 0 8px 18px; color: #CBD5E1;'>
                            {''.join([f"<li>{c}</li>" for c in rec['key_concepts']])}
                        </ul>
                    </div>
                    <div style='background: rgba(15, 23, 42, 0.4); border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; font-size: 13px;'>
                        <strong style='color:#34D399;'>🛠️ Hands-on Project Blueprint:</strong><br>
                        <span style='color:#E2E8F0;'>{rec['project_idea']}</span>
                    </div>
                    <div style='font-size:12px; color:#94A3B8; margin-top:6px;'>
                        <strong>Recommended Resource:</strong> {rec['recommended_resource']}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ==============================================================================
# PAGE 7: ⚖️ CANDIDATE COMPARISON
# ==============================================================================
elif st.session_state.current_page == "⚖️ Candidate Comparison":
    st.markdown("## ⚖️ Side-by-Side Candidate Comparison")
    st.caption("Compare qualifications, matched competencies, and score breakdowns across shortlisted candidates.")

    ranked = st.session_state.ranked_results
    if not ranked:
        st.warning("Please run a screening analysis first to compare candidates.")
    else:
        valid_candidates = [c for c in ranked if c.get("status") == "Processed"]
        cand_names = [c["candidate_name"] for c in valid_candidates]

        if len(cand_names) < 2:
            st.info("At least two successfully processed candidates are required for side-by-side comparison.")
        else:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                cand_a_name = st.selectbox("Select Candidate A:", cand_names, index=0)
            with col_sel2:
                cand_b_name = st.selectbox("Select Candidate B:", cand_names, index=1 if len(cand_names) > 1 else 0)

            cand_a = next(c for c in valid_candidates if c["candidate_name"] == cand_a_name)
            cand_b = next(c for c in valid_candidates if c["candidate_name"] == cand_b_name)

            facts_a = extract_candidate_profile_facts(cand_a.get("raw_text") or cand_a.get("clean_text") or "")
            facts_b = extract_candidate_profile_facts(cand_b.get("raw_text") or cand_b.get("clean_text") or "")

            st.markdown("<br>", unsafe_allow_html=True)

            # Side by side cards
            comp1, comp2 = st.columns(2, gap="large")
            with comp1:
                badge_a_color = "#10B981" if cand_a.get("is_shortlisted") else "#F59E0B"
                st.markdown(f"""
                <div class='glass-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <h3 style='margin:0; font-size:22px;'>{cand_a['candidate_name']}</h3>
                        <span style='background:{badge_a_color}; color:#fff; font-weight:700; font-size:11px; padding:4px 10px; border-radius:12px;'>
                            {'SHORTLISTED' if cand_a.get('is_shortlisted') else 'UNDER REVIEW'}
                        </span>
                    </div>
                    <div style='font-size:12px; color:#94A3B8; margin-top:4px;'>Rank #{cand_a['rank']} &middot; {cand_a['metadata'].get('email') or 'No email'}</div>
                    <hr style='border-color: rgba(255,255,255,0.08); margin: 12px 0;'>
                    <div style='font-size:28px; font-weight:800; color:#38BDF8;'>{cand_a['composite_score']}%</div>
                    <div style='font-size:11px; text-transform:uppercase; color:#94A3B8;'>Composite Match Score</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Semantic Sim**: `{cand_a['semantic_score_pct']}%` &middot; **Skill Coverage**: `{cand_a['skill_match_pct']}%`")
                st.markdown(f"**Est. Experience**: `{facts_a.get('years_of_experience_est', 'Not stated')} yrs`")
                st.markdown(f"**Education**: `{facts_a['degrees'][0]['level'] if facts_a.get('degrees') else 'Not stated'}`")
                st.markdown("##### Matched Skills:")
                st.markdown(render_skill_badges(cand_a.get("matched_skills", []), "matched"), unsafe_allow_html=True)

            with comp2:
                badge_b_color = "#10B981" if cand_b.get("is_shortlisted") else "#F59E0B"
                st.markdown(f"""
                <div class='glass-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <h3 style='margin:0; font-size:22px;'>{cand_b['candidate_name']}</h3>
                        <span style='background:{badge_b_color}; color:#fff; font-weight:700; font-size:11px; padding:4px 10px; border-radius:12px;'>
                            {'SHORTLISTED' if cand_b.get('is_shortlisted') else 'UNDER REVIEW'}
                        </span>
                    </div>
                    <div style='font-size:12px; color:#94A3B8; margin-top:4px;'>Rank #{cand_b['rank']} &middot; {cand_b['metadata'].get('email') or 'No email'}</div>
                    <hr style='border-color: rgba(255,255,255,0.08); margin: 12px 0;'>
                    <div style='font-size:28px; font-weight:800; color:#818CF8;'>{cand_b['composite_score']}%</div>
                    <div style='font-size:11px; text-transform:uppercase; color:#94A3B8;'>Composite Match Score</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"**Semantic Sim**: `{cand_b['semantic_score_pct']}%` &middot; **Skill Coverage**: `{cand_b['skill_match_pct']}%`")
                st.markdown(f"**Est. Experience**: `{facts_b.get('years_of_experience_est', 'Not stated')} yrs`")
                st.markdown(f"**Education**: `{facts_b['degrees'][0]['level'] if facts_b.get('degrees') else 'Not stated'}`")
                st.markdown("##### Matched Skills:")
                st.markdown(render_skill_badges(cand_b.get("matched_skills", []), "matched"), unsafe_allow_html=True)

            st.markdown("---")

            # Comparative Matrix: Overlapping vs Distinct Skills
            skills_a = set(cand_a.get("matched_skills", []))
            skills_b = set(cand_b.get("matched_skills", []))
            common = sorted(list(skills_a.intersection(skills_b)))
            unique_a = sorted(list(skills_a - skills_b))
            unique_b = sorted(list(skills_b - skills_a))

            st.markdown("#### 🎯 Skill Overlap & Differentiators")
            o1, o2, o3 = st.columns(3)
            with o1:
                st.markdown(f"**Shared Capabilities ({len(common)})**")
                st.markdown(render_skill_badges(common, "matched"), unsafe_allow_html=True)
            with o2:
                st.markdown(f"**Unique to {cand_a['candidate_name']} ({len(unique_a)})**")
                st.markdown(render_skill_badges(unique_a, "bonus"), unsafe_allow_html=True)
            with o3:
                st.markdown(f"**Unique to {cand_b['candidate_name']} ({len(unique_b)})**")
                st.markdown(render_skill_badges(unique_b, "bonus"), unsafe_allow_html=True)


# ==============================================================================
# PAGE 8: 📈 ANALYTICS
# ==============================================================================
elif st.session_state.current_page == "📈 Analytics":
    st.markdown("## 📈 Deep-Dive Talent Analytics & Pipeline Telemetry")
    st.caption("Distribution profiles, correlation analysis, and candidate competency metrics.")

    ranked = st.session_state.ranked_results
    if not ranked:
        st.warning("Please run a screening analysis first to explore analytics.")
        if st.button("🚀 Load Instant Demo Candidates", type="primary"):
            with st.spinner("Loading demo candidate resumes..."):
                load_demo_data_action(model, semantic_wt, skill_wt, shortlist_cutoff)
                st.rerun()
    else:
        valid_candidates = [c for c in ranked if c.get("status") == "Processed"]

        # Bracket breakdown
        tier_high = len([c for c in valid_candidates if c["composite_score"] >= 75])
        tier_mid = len([c for c in valid_candidates if 50 <= c["composite_score"] < 75])
        tier_low = len([c for c in valid_candidates if c["composite_score"] < 50])

        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown(render_stat_card_html(str(tier_high), "High Fit (≥75%)", "🌟", "Shortlist Pool", "positive"), unsafe_allow_html=True)
        with b2:
            st.markdown(render_stat_card_html(str(tier_mid), "Moderate Fit (50-74%)", "⚖️", "Review Pool", "positive"), unsafe_allow_html=True)
        with b3:
            st.markdown(render_stat_card_html(str(tier_low), "Low Alignment (<50%)", "📉", "Upskilling Target", "positive"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Correlation Table / Data View
        st.markdown("#### 🔬 Detailed Score Correlation & Breakdown")
        analytics_df = pd.DataFrame([
            {
                "Candidate": c["candidate_name"],
                "Composite (%)": c["composite_score"],
                "Semantic Sim (%)": c["semantic_score_pct"],
                "Skill Match (%)": c["skill_match_pct"],
                "Matched Skills Count": len(c.get("matched_skills", [])),
                "Missing Skills Count": len(c.get("missing_skills", [])),
                "Decision": "SHORTLISTED" if c.get("is_shortlisted") else "UNDER REVIEW"
            }
            for c in valid_candidates
        ])
        st.dataframe(analytics_df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown("##### Score Component Comparison")
            c_data = analytics_df.set_index("Candidate")[["Composite (%)", "Semantic Sim (%)", "Skill Match (%)"]]
            st.line_chart(c_data)
        with c2:
            st.markdown("##### Matched vs Missing Skill Ratio")
            m_data = analytics_df.set_index("Candidate")[["Matched Skills Count", "Missing Skills Count"]]
            st.bar_chart(m_data)


# ==============================================================================
# PAGE 9: 📄 REPORTS
# ==============================================================================
elif st.session_state.current_page == "📄 Reports":
    st.markdown("## 📄 Recruitment Screening Reports & Export Studio")
    st.caption("Generate compliant audit reports, sanitize CSV data for security, and download candidate packages.")

    ranked = st.session_state.ranked_results
    if not ranked:
        st.warning("Please run a screening analysis first to generate reports.")
        if st.button("🚀 Load Instant Demo Candidates", type="primary"):
            with st.spinner("Loading demo candidate resumes..."):
                load_demo_data_action(model, semantic_wt, skill_wt, shortlist_cutoff)
                st.rerun()
    else:
        valid_candidates = [c for c in ranked if c.get("status") == "Processed"]
        shortlisted = [c for c in valid_candidates if c.get("is_shortlisted")]

        # Executive Summary Box
        st.markdown(f"""
        <div class='glass-card'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <h3 style='margin:0; font-size:22px;'>Executive Talent Acquisition Summary</h3>
                    <div style='font-size:13px; color:#94A3B8; margin-top:4px;'>Role: {st.session_state.selected_preset} &middot; Total Candidates: {len(valid_candidates)}</div>
                </div>
                <div>
                    <span style='background:rgba(16, 185, 129, 0.15); color:#34D399; font-weight:800; font-size:12px; padding:6px 14px; border-radius:20px;'>
                        Audit Ready
                    </span>
                </div>
            </div>
            <hr style='border-color: rgba(255,255,255,0.08); margin: 16px 0;'>
            <div style='display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px;'>
                <div>
                    <div style='font-size:12px; color:#94A3B8; text-transform:uppercase;'>Recommended for Interview</div>
                    <div style='font-size:22px; font-weight:800; color:#34D399;'>{len(shortlisted)} Candidates</div>
                </div>
                <div>
                    <div style='font-size:12px; color:#94A3B8; text-transform:uppercase;'>Top Candidate Match</div>
                    <div style='font-size:22px; font-weight:800; color:#38BDF8;'>{valid_candidates[0]['candidate_name'] if valid_candidates else 'None'}</div>
                </div>
                <div>
                    <div style='font-size:12px; color:#94A3B8; text-transform:uppercase;'>Average Pipeline Score</div>
                    <div style='font-size:22px; font-weight:800; color:#F8FAFC;'>{(sum(c['composite_score'] for c in valid_candidates)/len(valid_candidates)):.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Download Buttons
        st.markdown("#### 📥 Export Formats")
        csv_data = generate_csv_report(ranked, jd_title=st.session_state.selected_preset)
        
        rep_c1, rep_c2 = st.columns([1, 1])
        with rep_c1:
            st.download_button(
                label="📥 Download Full Screening Report (CSV with Sanitization)",
                data=csv_data,
                file_name="resumerank_ai_full_report.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        with rep_c2:
            st.caption("🔒 **CSV Formula Protection**: Prepends safe quotes to values starting with `=`, `+`, `-`, or `@` to eliminate formula injection risks in Excel.")

        # Candidate Summary Table
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📋 Executive Audit Table")
        rep_df = pd.DataFrame([
            {
                "Rank": f"#{c['rank']}",
                "Candidate": c["candidate_name"],
                "Composite Match": f"{c['composite_score']:.1f}%",
                "Semantic Sim": f"{c['semantic_score_pct']:.1f}%",
                "Skill Match": f"{c['skill_match_pct']:.1f}%",
                "Recommendation": "SHORTLISTED" if c.get("is_shortlisted") else "UNDER REVIEW"
            }
            for c in valid_candidates
        ])
        st.dataframe(rep_df, use_container_width=True, hide_index=True)


# ==============================================================================
# PAGE 10: ⚙️ PROFILE AND SETTINGS
# ==============================================================================
elif st.session_state.current_page == "⚙️ Profile and Settings":
    st.markdown("## ⚙️ Recruiter Profile & System Settings")
    st.caption("Manage user preferences, display options, scoring parameters, and system architecture.")

    curr_u = st.session_state.user
    if not curr_u or not curr_u.get("is_authenticated"):
        st.warning("🔒 Please sign in to access your Profile and Settings.")
        if st.button("Go to User Login", type="primary"):
            st.session_state.current_page = "👤 User Login"
            st.rerun()
        st.stop()

    col_prof, col_pref = st.columns(2, gap="large")

    with col_prof:
        st.markdown("### 👤 Recruiter Profile")
        st.markdown(f"""
        <div class='glass-card'>
            <div style='display: flex; align-items: center; gap: 16px; margin-bottom: 18px;'>
                <div style='width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, #06B6D4, #7C3AED); display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; color: #fff;'>
                    {curr_u.get('full_name', 'U')[0]}
                </div>
                <div>
                    <h3 style='margin: 0; font-size: 20px; color: #F8FAFC;'>{curr_u.get('full_name')}</h3>
                    <div style='font-size: 13px; color: #38BDF8; font-weight: 600;'>{curr_u.get('role')}</div>
                    <div style='font-size: 12px; color: #94A3B8;'>{curr_u.get('email')}</div>
                </div>
            </div>
            <div style='font-size: 12px; color: #94A3B8;'>
                Provider: <strong>{curr_u.get('provider', 'SQLite Persistence')}</strong> &middot; Auth Status: <strong style='color:#34D399;'>Verified</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout of Current Session", type="secondary"):
            st.session_state.user = None
            st.success("Successfully logged out.")
            time.sleep(0.3)
            st.session_state.current_page = "🏠 Landing Page"
            st.rerun()

    with col_pref:
        st.markdown("### 🎨 Display & Theme Preferences")
        st.markdown("**Theme Selection:**")
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            if st.button("🌙 Dark Mode (Recommended)", use_container_width=True, type="primary" if st.session_state.theme == "dark" else "secondary"):
                st.session_state.theme = "dark"
                st.rerun()
        with p_c2:
            if st.button("☀️ Light Mode", use_container_width=True, type="primary" if st.session_state.theme == "light" else "secondary"):
                st.session_state.theme = "light"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Session Information:**")
        st.caption(f"- Resumes Staged in Session: **{len(st.session_state.parsed_resumes) if st.session_state.parsed_resumes else 0}**")
        st.caption(f"- Target Role Preset: **{st.session_state.selected_preset}**")
        st.caption(f"- Semantic Weight: **{st.session_state.semantic_wt * 100:.0f}%** &middot; Skill Weight: **{(1 - st.session_state.semantic_wt) * 100:.0f}%**")

    st.markdown("---")

    # Architecture Documentation
    st.markdown("### 🏛️ System Architecture & Production Deployment")
    st.markdown("""
    - **Dense Contextual Embeddings**: Uses `all-MiniLM-L6-v2` running natively via Sentence-Transformers on standard CPU.
    - **Zero External API Costs**: 100% on-premise execution; resumes are never transmitted to third-party proprietary APIs.
    - **GDPR & Fair Hiring Compliance**: Strips out demographic metadata; calculates scores purely from textual competence.
    - **Persistent SQLite Storage**: Relational schema storing users, resumes, screening logs, and jobs with bcrypt password protection.
    """)


# ==============================================================================
# PAGE ROUTING: ADMIN DASHBOARD & LOGIN PORTALS
# ==============================================================================
elif st.session_state.current_page == "🛡️ Admin Dashboard":
    render_admin_dashboard(st.session_state.user, cached_model=model)

elif st.session_state.current_page == "👤 User Login":
    render_user_login_page()

elif st.session_state.current_page == "📝 User Registration":
    render_user_registration_page()

elif st.session_state.current_page == "🛡️ Admin Login":
    render_admin_login_page()

elif st.session_state.current_page == "🔐 Login & Sign Up":
    # Backward-compatible redirect to User Login
    st.session_state.current_page = "👤 User Login"
    st.rerun()
