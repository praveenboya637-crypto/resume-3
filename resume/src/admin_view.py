"""
AI Resume Screening and Job Matching System - Administrator Dashboard & Governance View.
Features:
- Dashboard Overview: Metrics for Users, Resumes, Jobs, and Screening Operations.
- User Management: Search, inspect, activate/deactivate, delete users, and provision accounts.
- Resume Management: Monitor uploaded resume metadata, view skills, and manage records.
- Job Management: Add, edit, delete, and inspect system job descriptions.
- Platform Analytics: Database-driven charts, audit metrics, and CSV reporting.
- Admin Profile: Account details, password updates with bcrypt, and session controls.
- Distinct Purple / Dark Professional Theme.
"""

import time
import io
import pandas as pd
import streamlit as st
from typing import Dict, Any, List, Optional

from src.database import (
    db_get_user_metrics,
    db_get_all_users,
    db_set_user_status,
    db_delete_user,
    db_create_user,
    db_update_user_password,
    db_get_all_resumes,
    db_delete_resume_record,
    db_get_total_resumes_count,
    db_get_screening_records,
    db_get_screening_metrics,
    db_get_all_jobs,
    db_add_job,
    db_update_job,
    db_delete_job,
    db_get_total_jobs_count,
    db_get_user_by_id,
    verify_password_bcrypt
)
from src.auth import validate_password_strength, validate_email


def render_admin_dashboard(curr_user: Dict[str, Any], cached_model=None):
    """
    Renders the complete Administration Dashboard with purple/dark theme,
    governance controls, user management, and system-wide telemetry.
    """
    # Strict Authorization Guard: only authenticated accounts with admin role allowed
    if not curr_user or not curr_user.get("is_authenticated") or curr_user.get("role") != "admin":
        st.error("⛔ Access Denied: Administrator privileges required to access this portal.")
        if st.button("Return to Landing Page"):
            st.session_state.current_page = "🏠 Landing Page"
            st.rerun()
        return

    # Admin Portal Banner Header
    st.markdown(f"""
    <div class='admin-portal-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <div class='admin-badge'>
                    🛡️ Administrator Governance Portal &middot; Strict RBAC Active
                </div>
                <h1 style='margin: 8px 0 0 0; font-size: 32px; font-weight: 800; letter-spacing: -0.8px; color: #F8FAFC;'>
                    System <span style='background: linear-gradient(135deg, #C084FC, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Administration</span>
                </h1>
                <p style='margin: 6px 0 0 0; color: #C4B5FD; font-size: 14.5px;'>
                    Central governance hub for user lifecycle management, candidate resume tracking, job specifications, and screening audit telemetry.
                </p>
            </div>
            <div style='text-align: right;'>
                <div style='font-size: 12px; color: #A78BFA; font-weight: 700;'>LOGGED IN AS</div>
                <div style='font-size: 14px; font-weight: 800; color: #F8FAFC;'>{curr_user.get("full_name", "Administrator")}</div>
                <div style='font-size: 11px; color: #34D399; font-weight: 600;'>🟢 Superuser Verified</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Admin Portal Navigation Tabs
    admin_tabs = st.tabs([
        "📊 System Overview",
        "👥 User Management",
        "📁 Resume Management",
        "💼 Job Management",
        "📈 Analytics & Reports",
        "⚙️ Admin Profile"
    ])

    # ==========================================================================
    # TAB 1: SYSTEM OVERVIEW
    # ==========================================================================
    with admin_tabs[0]:
        st.markdown("### 📊 Platform Metrics & Telemetry")
        st.caption("Live metrics queried directly from the SQLite persistent database:")

        user_metrics = db_get_user_metrics()
        total_resumes = db_get_total_resumes_count()
        total_jobs = db_get_total_jobs_count()
        screening_metrics = db_get_screening_metrics()

        # 5 Key Metrics Cards (as required by section D)
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"""
            <div class='admin-card' style='text-align: center;'>
                <div style='font-size: 26px; margin-bottom: 4px;'>👥</div>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Total Registered</div>
                <div style='font-size: 32px; font-weight: 900; color: #F8FAFC;'>{user_metrics["total_users"]}</div>
                <div style='font-size: 11px; color: #A78BFA;'>Registered Accounts</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class='admin-card' style='text-align: center;'>
                <div style='font-size: 26px; margin-bottom: 4px;'>🟢</div>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Active Users</div>
                <div style='font-size: 32px; font-weight: 900; color: #34D399;'>{user_metrics["active_users"]}</div>
                <div style='font-size: 11px; color: #34D399;'>Permitted to Sign In</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class='admin-card' style='text-align: center;'>
                <div style='font-size: 26px; margin-bottom: 4px;'>📄</div>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Resumes Stored</div>
                <div style='font-size: 32px; font-weight: 900; color: #38BDF8;'>{total_resumes}</div>
                <div style='font-size: 11px; color: #38BDF8;'>Parsed Candidate Docs</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class='admin-card' style='text-align: center;'>
                <div style='font-size: 26px; margin-bottom: 4px;'>💼</div>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Jobs Analyzed</div>
                <div style='font-size: 32px; font-weight: 900; color: #FBBF24;'>{total_jobs}</div>
                <div style='font-size: 11px; color: #FBBF24;'>Active Specifications</div>
            </div>
            """, unsafe_allow_html=True)
        with m5:
            st.markdown(f"""
            <div class='admin-card' style='text-align: center;'>
                <div style='font-size: 26px; margin-bottom: 4px;'>⚡</div>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Screening Runs</div>
                <div style='font-size: 32px; font-weight: 900; color: #C084FC;'>{screening_metrics["total_screenings"]}</div>
                <div style='font-size: 11px; color: #C084FC;'>AI Matching Operations</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Overview Secondary Row: Quick Actions & Database Telemetry
        ov_c1, ov_c2 = st.columns([1.4, 1], gap="large")
        with ov_c1:
            st.markdown("#### ⚡ Administrator Operations")
            st.caption("Quickly jump to essential governance tasks:")

            q1, q2 = st.columns(2)
            with q1:
                st.markdown("""
                <div class='admin-card'>
                    <div style='font-size: 16px; font-weight: 800; color: #F8FAFC;'>👥 User Management</div>
                    <div style='font-size: 12.5px; color: #C4B5FD; margin: 4px 0 12px 0;'>
                        Manage registered accounts, toggle access, and review user activity logs.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with q2:
                st.markdown("""
                <div class='admin-card'>
                    <div style='font-size: 16px; font-weight: 800; color: #F8FAFC;'>💼 Job Specifications</div>
                    <div style='font-size: 12.5px; color: #C4B5FD; margin: 4px 0 12px 0;'>
                        Create and calibrate role criteria, skill requirements, and target profiles.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            q3, q4 = st.columns(2)
            with q3:
                st.markdown("""
                <div class='admin-card'>
                    <div style='font-size: 16px; font-weight: 800; color: #F8FAFC;'>📁 Resume Audit</div>
                    <div style='font-size: 12.5px; color: #C4B5FD; margin: 4px 0 12px 0;'>
                        Inspect metadata, word counts, and extracted skills across all uploaded files.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with q4:
                st.markdown("""
                <div class='admin-card'>
                    <div style='font-size: 16px; font-weight: 800; color: #F8FAFC;'>📊 Platform Analytics</div>
                    <div style='font-size: 12.5px; color: #C4B5FD; margin: 4px 0 12px 0;'>
                        Download compliance audit logs and inspect candidate scoring distributions.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with ov_c2:
            st.markdown("#### 🛡️ Database & Security Telemetry")
            st.markdown(f"""
            <div style='background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 16px; padding: 20px;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                    <span style='font-size: 13px; font-weight: 700; color: #E2E8F0;'>Database Storage</span>
                    <span style='font-size: 11px; background: rgba(52, 211, 153, 0.15); color: #34D399; font-weight: 800; padding: 2px 8px; border-radius: 12px;'>SQLite 3 Persistent</span>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                    <span style='font-size: 13px; font-weight: 700; color: #E2E8F0;'>Password Encryption</span>
                    <span style='font-size: 11px; background: rgba(192, 132, 252, 0.15); color: #C084FC; font-weight: 800; padding: 2px 8px; border-radius: 12px;'>Bcrypt (Salted, 12 Rounds)</span>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                    <span style='font-size: 13px; font-weight: 700; color: #E2E8F0;'>Access Control</span>
                    <span style='font-size: 11px; background: rgba(56, 189, 248, 0.15); color: #38BDF8; font-weight: 800; padding: 2px 8px; border-radius: 12px;'>Strict Server-Side RBAC</span>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 13px; font-weight: 700; color: #E2E8F0;'>Neural Inference</span>
                    <span style='font-size: 11px; background: rgba(251, 191, 36, 0.15); color: #FBBF24; font-weight: 800; padding: 2px 8px; border-radius: 12px;'>384-D Local CPU</span>
                </div>
                <hr style='border: none; border-top: 1px solid rgba(168, 85, 247, 0.2); margin: 14px 0;' />
                <div style='font-size: 11px; color: #94A3B8; line-height: 1.5;'>
                    🔒 Plaintext passwords are never logged or stored. Public accounts cannot escalate privileges.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================================================
    # TAB 2: USER MANAGEMENT
    # ==========================================================================
    with admin_tabs[1]:
        st.markdown("### 👥 User Account Management")
        st.caption("View registered users, search accounts, activate/deactivate access, or remove accounts. Passwords are never displayed.")

        # Top Control Row: Search & Add User Expander
        u_search_col, u_filter_col = st.columns([2, 1])
        with u_search_col:
            user_search = st.text_input("🔍 Search Users (by Name, Email, or Role):", placeholder="e.g. sarah, @airesume.com, recruiter")
        with u_filter_col:
            status_filter = st.selectbox("Filter Status:", ["All", "Active", "Inactive / Suspended"])

        # Fetch users from SQLite
        all_users = db_get_all_users(search_query=user_search if user_search else None)

        if status_filter == "Active":
            all_users = [u for u in all_users if u.get("status") == "active"]
        elif status_filter == "Inactive / Suspended":
            all_users = [u for u in all_users if u.get("status") != "active"]

        st.markdown(f"**Found {len(all_users)} user account(s):**")

        # Table Display & Actions
        for u in all_users:
            u_id = u["id"]
            u_email = u["email"]
            u_name = u["full_name"]
            u_role = u["role"]
            u_status = u.get("status", "active")
            u_created = u.get("created_at", "N/A")
            u_last = u.get("last_login") or "Never"

            status_badge_color = "#34D399" if u_status == "active" else "#F43F5E"
            role_badge_bg = "rgba(168, 85, 247, 0.2)" if u_role == "admin" else "rgba(56, 189, 248, 0.15)"
            role_badge_color = "#C084FC" if u_role == "admin" else "#38BDF8"

            with st.container():
                st.markdown(f"""
                <div style='background: rgba(30, 27, 75, 0.4); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 14px; padding: 14px 18px; margin-bottom: 12px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='font-size: 15px; font-weight: 800; color: #F8FAFC;'>{u_name}</span>
                            <span style='margin-left: 8px; font-size: 11px; background: {role_badge_bg}; color: {role_badge_color}; font-weight: 800; padding: 2px 10px; border-radius: 10px;'>{u_role.upper()}</span>
                            <span style='margin-left: 6px; font-size: 11px; color: {status_badge_color}; font-weight: 700;'>● {u_status.upper()}</span>
                            <div style='font-size: 12.5px; color: #C4B5FD; margin-top: 3px;'>
                                📧 {u_email} &middot; <span style='color: #94A3B8;'>ID: {u_id}</span>
                            </div>
                            <div style='font-size: 11px; color: #94A3B8; margin-top: 2px;'>
                                Registered: {u_created} &middot; Last Login: {u_last}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                act_c1, act_c2, act_c3 = st.columns([1, 1, 2])
                with act_c1:
                    # Toggle Status Button
                    if u_status == "active":
                        if st.button(f"⏸️ Deactivate", key=f"btn_deact_{u_id}", use_container_width=True):
                            succ, msg = db_set_user_status(u_id, "inactive")
                            if succ:
                                st.success(msg)
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        if st.button(f"▶️ Activate", key=f"btn_act_{u_id}", use_container_width=True):
                            succ, msg = db_set_user_status(u_id, "active")
                            if succ:
                                st.success(msg)
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.error(msg)

                with act_c2:
                    # Delete with confirmation
                    with st.popover(f"🗑️ Delete Account"):
                        st.warning(f"Are you sure you want to permanently delete **{u_name}** ({u_email})?")
                        if st.button("Confirm Delete", key=f"conf_del_{u_id}", type="primary"):
                            succ, msg = db_delete_user(u_id)
                            if succ:
                                st.success(msg)
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.error(msg)
                with act_c3:
                    st.empty()

        st.markdown("---")

        # Provision New User Form
        with st.expander("➕ Provision New Account Directly (Admin Console)", expanded=False):
            st.caption("Manually create a user or recruiter account with pre-set credentials:")
            with st.form("admin_create_user_form"):
                new_u_name = st.text_input("Full Name:", placeholder="e.g. Marcus Vance")
                new_u_email = st.text_input("Email Address:", placeholder="e.g. marcus@company.com")
                new_u_role = st.selectbox("Role Assignment:", ["user", "admin"])
                new_u_pass = st.text_input("Initial Password (min 6 characters):", type="password")

                create_submitted = st.form_submit_button("Create Account in Database", type="primary")
                if create_submitted:
                    if not new_u_name or not new_u_email or not new_u_pass:
                        st.error("Please fill in all fields.")
                    elif not validate_email(new_u_email):
                        st.error("Invalid email format.")
                    else:
                        is_strong, pwd_err = validate_password_strength(new_u_pass)
                        if not is_strong:
                            st.error(pwd_err)
                        else:
                            succ, u_data, msg = db_create_user(new_u_email, new_u_pass, new_u_name, role=new_u_role)
                            if succ:
                                st.success(f"Account created successfully for {new_u_name} ({new_u_role})!")
                                time.sleep(0.4)
                                st.rerun()
                            else:
                                st.error(msg)

    # ==========================================================================
    # TAB 3: RESUME MANAGEMENT
    # ==========================================================================
    with admin_tabs[2]:
        st.markdown("### 📁 Resume Management & Governance")
        st.caption("Inspect candidate resume records, parsed word counts, extracted skill metadata, and status.")

        resumes = db_get_all_resumes(limit=100)

        if not resumes:
            st.info("ℹ️ No resumes uploaded yet. Resumes uploaded by users in Resume Screening or created in Resume Builder will appear here.")
        else:
            st.markdown(f"**Total Tracked Resumes ({len(resumes)}):**")
            for r in resumes:
                r_id = r["id"]
                r_fname = r["filename"]
                r_cand = r.get("candidate_name") or "Unnamed Candidate"
                r_email = r.get("extracted_email") or "None detected"
                r_wc = r.get("word_count", 0)
                r_date = r.get("uploaded_at", "N/A")
                r_owner = r.get("owner_email") or "System / Demo"

                try:
                    import json
                    r_skills = json.loads(r.get("skills_detected") or "[]")
                except Exception:
                    r_skills = []

                with st.container():
                    st.markdown(f"""
                    <div style='background: rgba(30, 27, 75, 0.4); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 12px; padding: 14px 18px; margin-bottom: 10px;'>
                        <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                            <strong style='font-size: 14.5px; color: #F8FAFC;'>📄 {r_fname}</strong>
                            <span style='font-size: 11px; color: #94A3B8;'>Uploaded: {r_date}</span>
                        </div>
                        <div style='font-size: 12.5px; color: #C4B5FD; margin-top: 4px;'>
                            Candidate: <b>{r_cand}</b> &middot; Contact: <b>{r_email}</b> &middot; Words: <b>{r_wc}</b> &middot; Uploader: <b>{r_owner}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    r_col1, r_col2 = st.columns([3, 1])
                    with r_col1:
                        if r_skills:
                            skills_pills = "".join([f"<span class='badge-pill badge-matched'>{s}</span>" for s in r_skills[:8]])
                            st.markdown(skills_pills, unsafe_allow_html=True)
                        else:
                            st.caption("No taxonomy skills extracted.")
                    with r_col2:
                        with st.popover(f"🗑️ Delete Record"):
                            st.warning(f"Delete record for '{r_fname}'?")
                            if st.button("Confirm", key=f"del_res_{r_id}", type="primary"):
                                if db_delete_resume_record(r_id):
                                    st.success("Resume record removed.")
                                    time.sleep(0.3)
                                    st.rerun()

    # ==========================================================================
    # TAB 4: JOB MANAGEMENT
    # ==========================================================================
    with admin_tabs[3]:
        st.markdown("### 💼 Job Specifications Management")
        st.caption("Add, calibrate, or remove job criteria and requirements used by the screening engine.")

        # Add New Job Form Expander
        with st.expander("➕ Add New Job Specification", expanded=False):
            with st.form("add_job_form"):
                j_title = st.text_input("Job Title *", placeholder="e.g. Senior Backend Engineer (Go & Distributed Systems)")
                j_dept = st.text_input("Department:", value="Engineering")
                j_exp = st.text_input("Experience Level:", value="Senior (4+ Yrs)")
                j_desc = st.text_area("Job Requirements & Qualifications *", height=150, placeholder="Describe required skills, responsibilities, and qualifications...")

                submit_job = st.form_submit_button("Save Job Specification", type="primary")
                if submit_job:
                    if not j_title or not j_desc:
                        st.error("Job title and requirements description are required.")
                    else:
                        succ, msg, new_id = db_add_job(j_title, j_desc, j_dept, j_exp, created_by=curr_user.get("email", "admin"))
                        if succ:
                            st.success(msg)
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(msg)

        # Existing Jobs Display & Edit/Delete Controls
        jobs = db_get_all_jobs()
        st.markdown(f"**Managed Job Specifications ({len(jobs)}):**")

        for job in jobs:
            j_id = job["id"]
            title = job["title"]
            dept = job["department"]
            exp = job["experience_level"]
            desc = job["description"]

            with st.expander(f"💼 {title} ({dept} &middot; {exp})"):
                with st.form(f"edit_job_{j_id}"):
                    edit_title = st.text_input("Job Title:", value=title, key=f"jt_{j_id}")
                    edit_dept = st.text_input("Department:", value=dept, key=f"jd_{j_id}")
                    edit_exp = st.text_input("Experience Level:", value=exp, key=f"je_{j_id}")
                    edit_desc = st.text_area("Description / Criteria:", value=desc, height=130, key=f"jdesc_{j_id}")

                    c_save, c_del = st.columns([1, 1])
                    with c_save:
                        if st.form_submit_button("💾 Save Updates", type="primary"):
                            succ, msg = db_update_job(j_id, edit_title, edit_desc, edit_dept, edit_exp)
                            if succ:
                                st.success(msg)
                                time.sleep(0.3)
                                st.rerun()
                            else:
                                st.error(msg)

                # Delete Job Button outside the form
                with st.popover(f"🗑️ Delete Specification"):
                    st.warning(f"Permanently delete '{title}'?")
                    if st.button("Confirm Delete", key=f"del_job_{j_id}", type="primary"):
                        succ, msg = db_delete_job(j_id)
                        if succ:
                            st.success(msg)
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error(msg)

    # ==========================================================================
    # TAB 5: ANALYTICS & REPORTS
    # ==========================================================================
    with admin_tabs[4]:
        st.markdown("### 📈 Platform Analytics & Audit Reports")
        st.caption("Real database analytics covering user registration volume, screening accuracy, and audit exports.")

        user_metrics = db_get_user_metrics()
        screening_metrics = db_get_screening_metrics()
        all_screenings = db_get_screening_records(limit=200)

        # Analytics Cards Row
        an1, an2, an3 = st.columns(3)
        with an1:
            st.markdown(f"""
            <div class='admin-card'>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Account Ratio</div>
                <div style='font-size: 26px; font-weight: 900; color: #F8FAFC;'>{user_metrics['user_count']} Users &middot; {user_metrics['admin_count']} Admins</div>
                <div style='font-size: 11px; color: #34D399; margin-top: 4px;'>{round(user_metrics['active_users']/max(user_metrics['total_users'],1)*100, 0):.0f}% Active Accounts</div>
            </div>
            """, unsafe_allow_html=True)
        with an2:
            st.markdown(f"""
            <div class='admin-card'>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Average Match Score</div>
                <div style='font-size: 26px; font-weight: 900; color: #38BDF8;'>{screening_metrics['avg_composite_score']}%</div>
                <div style='font-size: 11px; color: #94A3B8; margin-top: 4px;'>Across all neural screening sessions</div>
            </div>
            """, unsafe_allow_html=True)
        with an3:
            st.markdown(f"""
            <div class='admin-card'>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 700;'>Shortlist Conversion</div>
                <div style='font-size: 26px; font-weight: 900; color: #C084FC;'>{screening_metrics['shortlisted_count']} Shortlisted</div>
                <div style='font-size: 11px; color: #A78BFA; margin-top: 4px;'>{screening_metrics['review_count']} Under Review</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Database Telemetry Charts
        ch_c1, ch_c2 = st.columns(2, gap="medium")
        with ch_c1:
            st.markdown("#### 📊 Screening Match Score Distribution")
            if all_screenings:
                scores = [float(s["composite_score"]) for s in all_screenings]
                bins = [0, 40, 60, 75, 85, 100]
                labels = ["<40% (Poor)", "40-59% (Fair)", "60-74% (Good)", "75-84% (Strong)", "85-100% (Top Tier)"]
                score_series = pd.cut(scores, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index()
                st.bar_chart(score_series, color="#A855F7")
            else:
                st.info("ℹ️ No screening operations recorded yet to chart.")

        with ch_c2:
            st.markdown("#### 👥 User Role & Governance Breakdown")
            user_chart_df = pd.DataFrame([
                {"Category": "Active Users", "Count": user_metrics["active_users"]},
                {"Category": "Inactive Users", "Count": user_metrics["inactive_users"]},
                {"Category": "Regular Users", "Count": user_metrics["user_count"]},
                {"Category": "Administrators", "Count": user_metrics["admin_count"]},
            ]).set_index("Category")
            st.bar_chart(user_chart_df, color="#38BDF8")

        st.markdown("<br>", unsafe_allow_html=True)

        # CSV Download Exports
        st.markdown("#### 📥 Administrative Audit Data Exports")
        st.caption("Export authoritative CSV records directly from the SQLite database for compliance:")

        exp_c1, exp_c2, exp_c3 = st.columns(3)

        with exp_c1:
            # Export Users
            users_list = db_get_all_users()
            if users_list:
                users_df = pd.DataFrame(users_list)
                csv_users = users_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Export Users (CSV)",
                    data=csv_users,
                    file_name="TalentIQ_Registered_Users_Audit.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with exp_c2:
            # Export Resumes
            res_list = db_get_all_resumes(limit=500)
            if res_list:
                res_df = pd.DataFrame(res_list)
                csv_res = res_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Export Resumes (CSV)",
                    data=csv_res,
                    file_name="TalentIQ_Candidate_Resumes_Audit.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with exp_c3:
            # Export Screening Records
            if all_screenings:
                scr_df = pd.DataFrame(all_screenings)
                csv_scr = scr_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Export Screenings (CSV)",
                    data=csv_scr,
                    file_name="TalentIQ_Screening_History_Audit.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # ==========================================================================
    # TAB 6: ADMIN PROFILE & SECURITY
    # ==========================================================================
    with admin_tabs[5]:
        st.markdown("### ⚙️ Administrator Profile & Security")
        st.caption("Manage administrator account details, update your bcrypt password, and manage active sessions.")

        prof_c1, prof_c2 = st.columns([1, 1.2], gap="large")

        with prof_c1:
            st.markdown(f"""
            <div class='admin-card'>
                <div style='font-size: 11px; text-transform: uppercase; color: #C4B5FD; font-weight: 800; letter-spacing: 0.5px;'>ACCOUNT METADATA</div>
                <div style='font-size: 20px; font-weight: 800; color: #F8FAFC; margin-top: 6px;'>{curr_user.get("full_name")}</div>
                <div style='font-size: 13px; color: #A78BFA; margin-top: 2px;'>{curr_user.get("email")}</div>
                <hr style='border: none; border-top: 1px solid rgba(168, 85, 247, 0.25); margin: 12px 0;' />
                <div style='font-size: 12px; color: #E2E8F0; line-height: 1.8;'>
                    <div><b>Role:</b> <span style='color: #C084FC;'>{curr_user.get("role", "admin").upper()}</span></div>
                    <div><b>ID:</b> <span style='color: #94A3B8;'>{curr_user.get("id")}</span></div>
                    <div><b>Status:</b> <span style='color: #34D399;'>● ACTIVE</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚪 Sign Out of Administrator Portal", type="secondary", use_container_width=True):
                st.session_state.user = None
                st.session_state.current_page = "🏠 Landing Page"
                st.success("Signed out successfully.")
                time.sleep(0.3)
                st.rerun()

        with prof_c2:
            st.markdown("#### 🔑 Update Administrator Password")
            st.caption("Hashes your new password using bcrypt before persisting to SQLite.")

            with st.form("admin_change_password_form"):
                current_pwd = st.text_input("Current Administrator Password *", type="password")
                new_pwd = st.text_input("New Password (min 6 characters) *", type="password")
                confirm_new_pwd = st.text_input("Confirm New Password *", type="password")

                pwd_submitted = st.form_submit_button("Update Password", type="primary")

                if pwd_submitted:
                    if not current_pwd or not new_pwd or not confirm_new_pwd:
                        st.error("Please fill in all password fields.")
                    elif new_pwd != confirm_new_pwd:
                        st.error("New passwords do not match. Please re-enter.")
                    else:
                        is_strong, err_msg = validate_password_strength(new_pwd)
                        if not is_strong:
                            st.error(err_msg)
                        else:
                            # Verify current password
                            db_user = db_get_user_by_id(curr_user.get("id"))
                            if not db_user or not verify_password_bcrypt(current_pwd, db_user.get("password_hash")):
                                st.error("Current password verification failed. Please try again.")
                            else:
                                if db_update_user_password(curr_user["id"], new_pwd):
                                    st.success("Administrator password successfully updated in SQLite database!")
                                    time.sleep(0.4)
                                else:
                                    st.error("Failed to update password. Please check database permissions.")

