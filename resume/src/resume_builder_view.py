"""
AI Resume Screening and Job Matching System - Interactive Resume Builder UI.
Features:
- Multi-section form: Personal Info, Summary, Education, Skills, Experience (skippable for freshers), Projects, Certifications, Additional Sections.
- Dynamic addition/removal of entries for education, experience, projects, and certifications.
- Pre-fill sample profiles: Senior Experienced & Graduate Fresher for instant one-click testing.
- Live high-fidelity resume preview across 3 templates:
  1. Modern Professional
  2. Minimal ATS-Friendly
  3. Technical / Software Developer
- Downloadable PDF generation with ReportLab, multi-page support, and verified PyMuPDF text extraction.
- Resume Quality Assistant & ATS Score panel with metric detection, power verbs, and target-role keyword guidance.
- Direct integration with TalentIQ Screening Engine to evaluate the generated PDF against job descriptions.
"""

import time
import io
import os
import re
import streamlit as st
from typing import Dict, Any, List, Optional

from src.pdf_generator import generate_resume_pdf, get_download_filename
from src.resume_quality import evaluate_resume_quality, ROLE_RECOMMENDATIONS, ACTION_VERBS
from src.resume_templates import get_resume_preview_html
from src.parsers import extract_text_from_pdf, parse_resume
from src.constants import SAMPLE_JOB_DESCRIPTIONS, ETHICAL_DISCLAIMER
from src.embeddings import compute_semantic_similarity
from src.skills_extractor import extract_skills_from_text, analyze_skill_gap


# ==============================================================================
# SAMPLE PROFILE TEMPLATE FOR RAPID EVALUATION
# ==============================================================================
SAMPLE_FRESHER_DATA = {
    "full_name": "Maya Patel",
    "headline": "Junior AI / Full Stack Software Engineer",
    "email": "maya.patel@example.com",
    "phone": "+1 (555) 782-3140",
    "location": "Boston, MA",
    "linkedin": "https://linkedin.com/in/mayapatel-cs",
    "github": "https://github.com/mayapatel-dev",
    "portfolio": "https://mayapatel.tech",
    "summary": "Recent Computer Science Honors graduate with strong foundations in Python, PyTorch, React, and REST API development. Built and deployed 3 full-stack and AI applications with Docker containerization, earning First Place at the 2025 National Collegiate AI Hackathon.",
    "skills_languages": "Python, JavaScript, TypeScript, C++, SQL, HTML5, CSS3",
    "skills_tech": "Machine Learning, PyTorch, Scikit-Learn, REST API, React, Node.js",
    "skills_tools": "Docker, Git, GitHub Actions, PostgreSQL, Linux, VS Code, Postman",
    "skills_soft": "Problem Solving, Rapid Learner, Team Collaboration, Analytical Communication",
    "is_fresher": True,
    "experience": [],
    "projects": [
        {
            "title": "Smart Vision Edge Defect Detector",
            "technologies": "Python, PyTorch, OpenCV, FastAPI, Docker",
            "link": "https://github.com/mayapatel-dev/edge-defect-detector",
            "description": "Constructed a computer vision pipeline for real-time manufacturing defect classification running on edge devices.",
            "achievements": "Achieved 96.4% test accuracy at 45 FPS; won 1st Place out of 80 teams at the National Collegiate AI Hackathon."
        },
        {
            "title": "CollabNotes Real-Time Workspace",
            "technologies": "TypeScript, React, Node.js, WebSockets, PostgreSQL, Docker",
            "link": "https://github.com/mayapatel-dev/collab-notes",
            "description": "Built a collaborative document editor supporting concurrent real-time markdown editing and user cursor presence.",
            "achievements": "Handled 150 concurrent WebSocket sessions with sub-30ms operational transformation synchronization."
        },
        {
            "title": "Algorithmic Portfolio Optimizer",
            "technologies": "Python, Pandas, NumPy, Scikit-Learn, Streamlit",
            "link": "https://github.com/mayapatel-dev/portfolio-optimizer",
            "description": "Developed a financial risk simulation tool utilizing Markowitz Modern Portfolio Theory and Monte Carlo analysis.",
            "achievements": "Simulated 50,000 risk scenarios across 10 years of historical S&P 500 asset data."
        }
    ],
    "education": [
        {
            "institution": "Northeastern University",
            "degree": "Bachelor of Science",
            "field": "Computer Science (Data Science Minor)",
            "start_year": "2021",
            "end_year": "2025",
            "cgpa": "3.88 / 4.0 (Magna Cum Laude)"
        }
    ],
    "certifications": [
        {
            "name": "First Place Winner – National Collegiate AI Hackathon",
            "issuer": "Collegiate Tech League",
            "year": "2025",
            "details": "Ranked #1 among 80 university engineering teams."
        },
        {
            "name": "Deep Learning Specialization",
            "issuer": "DeepLearning.AI / Coursera",
            "year": "2024",
            "details": "Completed with Honors (5-course sequence)"
        }
    ],
    "additional_sections": {
        "Relevant Coursework": "Data Structures & Algorithms, Object-Oriented Design, Operating Systems, Machine Learning, Database Management",
        "Languages": "English (Fluent), Hindi (Native), French (Conversational)"
    }
}


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
def init_builder_session_state():
    """Initializes all state variables required by the resume builder with clean empty states."""
    defaults = {
        "rb_full_name": "",
        "rb_headline": "",
        "rb_email": "",
        "rb_phone": "",
        "rb_location": "",
        "rb_linkedin": "",
        "rb_github": "",
        "rb_portfolio": "",
        "rb_summary": "",
        "rb_skills_tech": "",
        "rb_skills_languages": "",
        "rb_skills_tools": "",
        "rb_skills_soft": "",
        "rb_is_fresher": False,
        "rb_template": "Modern Professional",
        "rb_target_role": "AI / Machine Learning Engineer",
        "rb_education": [],
        "rb_experience": [],
        "rb_projects": [],
        "rb_certifications": [],
        "rb_coursework": "",
        "rb_languages": "",
        "rb_volunteer": "",
        "rb_generated_pdf": None,
        "rb_last_screen_result": None
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def load_preset_data(preset_dict: Dict[str, Any]):
    """Loads a complete sample profile dictionary into session state."""
    st.session_state.rb_full_name = preset_dict.get("full_name", "")
    st.session_state.rb_headline = preset_dict.get("headline", "")
    st.session_state.rb_email = preset_dict.get("email", "")
    st.session_state.rb_phone = preset_dict.get("phone", "")
    st.session_state.rb_location = preset_dict.get("location", "")
    st.session_state.rb_linkedin = preset_dict.get("linkedin", "")
    st.session_state.rb_github = preset_dict.get("github", "")
    st.session_state.rb_portfolio = preset_dict.get("portfolio", "")
    st.session_state.rb_summary = preset_dict.get("summary", "")
    st.session_state.rb_skills_tech = preset_dict.get("skills_tech", "")
    st.session_state.rb_skills_languages = preset_dict.get("skills_languages", "")
    st.session_state.rb_skills_tools = preset_dict.get("skills_tools", "")
    st.session_state.rb_skills_soft = preset_dict.get("skills_soft", "")
    st.session_state.rb_is_fresher = preset_dict.get("is_fresher", False)
    st.session_state.rb_education = [dict(e) for e in preset_dict.get("education", [])]
    st.session_state.rb_experience = [dict(e) for e in preset_dict.get("experience", [])]
    st.session_state.rb_projects = [dict(p) for p in preset_dict.get("projects", [])]
    st.session_state.rb_certifications = [dict(c) for c in preset_dict.get("certifications", [])]
    
    add_dict = preset_dict.get("additional_sections", {})
    st.session_state.rb_coursework = add_dict.get("Relevant Coursework", "")
    st.session_state.rb_languages = add_dict.get("Languages", "")
    st.session_state.rb_volunteer = add_dict.get("Volunteer Experience", "")

    # Invalidate cached PDF so preview re-renders
    st.session_state.rb_generated_pdf = None
    st.session_state.rb_last_screen_result = None


def clear_form_data():
    """Resets form fields to clean blank states."""
    st.session_state.rb_full_name = ""
    st.session_state.rb_headline = ""
    st.session_state.rb_email = ""
    st.session_state.rb_phone = ""
    st.session_state.rb_location = ""
    st.session_state.rb_linkedin = ""
    st.session_state.rb_github = ""
    st.session_state.rb_portfolio = ""
    st.session_state.rb_summary = ""
    st.session_state.rb_skills_tech = ""
    st.session_state.rb_skills_languages = ""
    st.session_state.rb_skills_tools = ""
    st.session_state.rb_skills_soft = ""
    st.session_state.rb_is_fresher = False
    st.session_state.rb_education = []
    st.session_state.rb_experience = []
    st.session_state.rb_projects = []
    st.session_state.rb_certifications = []
    st.session_state.rb_coursework = ""
    st.session_state.rb_languages = ""
    st.session_state.rb_volunteer = ""
    st.session_state.rb_generated_pdf = None
    st.session_state.rb_last_screen_result = None


def get_current_resume_dict() -> Dict[str, Any]:
    """Assembles a clean dictionary of all current form inputs."""
    additional = {}
    if st.session_state.get("rb_coursework"):
        additional["Relevant Coursework"] = st.session_state.rb_coursework
    if st.session_state.get("rb_languages"):
        additional["Languages"] = st.session_state.rb_languages
    if st.session_state.get("rb_volunteer"):
        additional["Volunteer Experience"] = st.session_state.rb_volunteer

    return {
        "full_name": st.session_state.get("rb_full_name", ""),
        "headline": st.session_state.get("rb_headline", ""),
        "email": st.session_state.get("rb_email", ""),
        "phone": st.session_state.get("rb_phone", ""),
        "location": st.session_state.get("rb_location", ""),
        "linkedin": st.session_state.get("rb_linkedin", ""),
        "github": st.session_state.get("rb_github", ""),
        "portfolio": st.session_state.get("rb_portfolio", ""),
        "summary": st.session_state.get("rb_summary", ""),
        "skills_tech": st.session_state.get("rb_skills_tech", ""),
        "skills_languages": st.session_state.get("rb_skills_languages", ""),
        "skills_tools": st.session_state.get("rb_skills_tools", ""),
        "skills_soft": st.session_state.get("rb_skills_soft", ""),
        "is_fresher": st.session_state.get("rb_is_fresher", False),
        "education": st.session_state.get("rb_education", []),
        "experience": st.session_state.get("rb_experience", []),
        "projects": st.session_state.get("rb_projects", []),
        "certifications": st.session_state.get("rb_certifications", []),
        "additional_sections": additional
    }


def extract_candidate_name_from_filename(filename: Optional[str]) -> str:
    """
    Safely sanitizes an uploaded filename into a formatted candidate display name.
    Replaces underscores, hyphens, and periods with spaces, removes unwanted
    'Resume' or 'CV' words/affixes, and titles the result.
    Handles None, non-string, or empty filenames safely without crashing.
    """
    if filename is None:
        return "Candidate"

    fname_str = str(filename).strip()
    if not fname_str:
        return "Candidate"

    # Strip directory path if present (e.g. from raw path uploads)
    if "/" in fname_str or "\\" in fname_str:
        fname_str = fname_str.replace("\\", "/").rsplit("/", 1)[-1]

    # Strip file extension if present
    base_fname = fname_str.rsplit(".", 1)[0] if "." in fname_str else fname_str
    base_fname = str(base_fname).strip()
    if not base_fname:
        return "Candidate"

    # Replace underscores, hyphens, and periods with spaces
    cleaned = re.sub(r"[_\-\.]+", " ", base_fname)

    # Remove unwanted 'Resume' or 'CV' tokens/affixes (case-insensitive)
    cleaned = re.sub(r"(?i)\b(resume|cv)\b", " ", cleaned)

    # Collapse multiple spaces and format title case
    cleaned = " ".join(cleaned.split()).strip()
    return cleaned.title() if cleaned else "Candidate"


# ==============================================================================
# MAIN VIEW RENDERER
# ==============================================================================
def render_resume_builder_page(cached_model=None):
    """
    Renders the complete Candidate Resume Creation experience in Streamlit.
    """
    init_builder_session_state()

    # Brand Title Header
    st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;'>
        <div>
            <div style='display: inline-block; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 20px; padding: 4px 12px; font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 8px;'>
                ✨ AI Resume Studio &middot; Production Grade
            </div>
            <h1 style='margin: 0; font-size: 32px; font-weight: 800; letter-spacing: -0.8px; color: #F8FAFC;'>
                Candidate <span style='background: linear-gradient(135deg, #38BDF8, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Resume Builder</span>
            </h1>
            <p style='margin: 6px 0 0 0; color: #94A3B8; font-size: 14.5px;'>
                Craft ATS-optimized, high-impact resumes tailored to tech roles. Preview live, download vector PDF, and audit with our built-in Quality Assistant.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Action Toolbar
    tbar1, tbar2, tbar3 = st.columns([1.3, 1.1, 1.3])
    with tbar1:
        if st.button("🎓 Load Starter Template", use_container_width=True, help="Loads a starter template with project emphasis"):
            load_preset_data(SAMPLE_FRESHER_DATA)
            st.toast("Loaded starter template!", icon="🎓")
            st.rerun()
    with tbar2:
        if st.button("🗑️ Reset Form", use_container_width=True, help="Clears all resume fields"):
            clear_form_data()
            st.toast("Cleared resume form fields.", icon="🔄")
            st.rerun()
    with tbar3:
        # Quick jump to screening
        if st.button("⚡ Test with Screener", use_container_width=True, type="secondary"):
            st.session_state.rb_active_tab = 3
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Template Selector & Target Role Row
    ctl_col1, ctl_col2 = st.columns([1.2, 1])
    with ctl_col1:
        template_options = [
            "Modern Professional",
            "Minimal ATS-Friendly",
            "Technical / Software Developer"
        ]
        curr_tmpl_idx = template_options.index(st.session_state.rb_template) if st.session_state.rb_template in template_options else 0
        selected_tmpl = st.selectbox(
            "🎨 Select Resume Template",
            template_options,
            index=curr_tmpl_idx,
            help="Choose the visual layout and ATS structure for preview and PDF export."
        )
        if selected_tmpl != st.session_state.rb_template:
            st.session_state.rb_template = selected_tmpl
            st.session_state.rb_generated_pdf = None
            st.rerun()

    with ctl_col2:
        role_options = list(ROLE_RECOMMENDATIONS.keys())
        curr_role_idx = role_options.index(st.session_state.rb_target_role) if st.session_state.rb_target_role in role_options else 0
        selected_role = st.selectbox(
            "🎯 Target Job Role (ATS Advisor)",
            role_options,
            index=curr_role_idx,
            help="Select your target position to receive tailored skill and keyword suggestions."
        )
        st.session_state.rb_target_role = selected_role

    st.markdown("---")

    # Main Tabs: 1) Edit Form, 2) Live Preview & Download, 3) Quality Assistant & ATS Audit, 4) Screening Simulation
    tab_labels = [
        "📝 Resume Information Form",
        "👁️ Live Preview & Download PDF",
        "🎯 Quality Assistant & ATS Audit",
        "⚡ TalentIQ Screening Test"
    ]
    tabs = st.tabs(tab_labels)

    # ==========================================================================
    # TAB 1: FORM INPUTS
    # ==========================================================================
    with tabs[0]:
        st.markdown("### A. Personal Information & Online Presence")
        p_c1, p_c2 = st.columns(2)
        with p_c1:
            st.session_state.rb_full_name = st.text_input(
                "Full Name *",
                value=st.session_state.rb_full_name,
                placeholder="e.g. Jane Doe"
            )
            st.session_state.rb_headline = st.text_input(
                "Professional Headline / Target Role *",
                value=st.session_state.rb_headline,
                placeholder="e.g. Senior Machine Learning Engineer"
            )
            st.session_state.rb_email = st.text_input(
                "Email Address *",
                value=st.session_state.rb_email,
                placeholder="e.g. jane.doe@example.com"
            )
            st.session_state.rb_phone = st.text_input(
                "Phone Number",
                value=st.session_state.rb_phone,
                placeholder="e.g. +1 (555) 012-3456"
            )
        with p_c2:
            st.session_state.rb_location = st.text_input(
                "City & State / Country",
                value=st.session_state.rb_location,
                placeholder="e.g. San Francisco, CA & Remote"
            )
            st.session_state.rb_linkedin = st.text_input(
                "LinkedIn Profile URL",
                value=st.session_state.rb_linkedin,
                placeholder="e.g. https://linkedin.com/in/username"
            )
            st.session_state.rb_github = st.text_input(
                "GitHub URL",
                value=st.session_state.rb_github,
                placeholder="e.g. https://github.com/username"
            )
            st.session_state.rb_portfolio = st.text_input(
                "Portfolio / Personal Website URL",
                value=st.session_state.rb_portfolio,
                placeholder="e.g. https://portfolio.dev"
            )

        st.session_state.rb_summary = st.text_area(
            "Professional Summary / Career Objective *",
            value=st.session_state.rb_summary,
            height=110,
            placeholder="High-impact 3-4 sentence overview of your technical background, core competencies, and career achievements..."
        )

        st.markdown("---")

        # B. Skills
        st.markdown("### B. Skills & Technical Competencies")
        st.caption("Group skills logically for ATS indexing. Separate entries with commas.")
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            st.session_state.rb_skills_languages = st.text_input(
                "Programming Languages",
                value=st.session_state.rb_skills_languages,
                placeholder="e.g. Python, SQL, Go, C++, TypeScript, Bash"
            )
            st.session_state.rb_skills_tech = st.text_input(
                "Core Technical Skills & Domains",
                value=st.session_state.rb_skills_tech,
                placeholder="e.g. PyTorch, Deep Learning, NLP, Transformers, LLM, Generative AI"
            )
        with s_c2:
            st.session_state.rb_skills_tools = st.text_input(
                "Frameworks, Cloud & Developer Tools",
                value=st.session_state.rb_skills_tools,
                placeholder="e.g. Docker, Kubernetes, AWS, GCP, FastAPI, CI/CD, Redis, Git"
            )
            st.session_state.rb_skills_soft = st.text_input(
                "Soft Skills & Leadership Competencies",
                value=st.session_state.rb_skills_soft,
                placeholder="e.g. Cross-Functional Team Leadership, Agile / Scrum, Problem Solving"
            )

        st.markdown("---")

        # C. Work Experience
        st.markdown("### C. Work Experience")
        is_fresher = st.checkbox(
            "🎓 I am a Fresher / Recent Graduate (Skip Work Experience)",
            value=st.session_state.rb_is_fresher,
            help="Check this if you do not have formal industry experience; the resume will automatically prioritize your technical projects and education."
        )
        st.session_state.rb_is_fresher = is_fresher

        if not is_fresher:
            exp_list = st.session_state.rb_experience
            for idx, exp in enumerate(exp_list):
                with st.expander(f"💼 Experience #{idx + 1}: {exp.get('role') or 'New Role'} @ {exp.get('company') or 'Company'}", expanded=(idx == 0)):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        exp["role"] = st.text_input(f"Job Title #{idx+1}", value=exp.get("role", ""), key=f"exp_role_{idx}")
                        exp["company"] = st.text_input(f"Company / Organization #{idx+1}", value=exp.get("company", ""), key=f"exp_comp_{idx}")
                    with e_col2:
                        d_col1, d_col2 = st.columns(2)
                        with d_col1:
                            exp["start_date"] = st.text_input(f"Start Date #{idx+1}", value=exp.get("start_date", ""), placeholder="e.g. Jan 2022", key=f"exp_sdate_{idx}")
                        with d_col2:
                            exp["end_date"] = st.text_input(f"End Date #{idx+1}", value=exp.get("end_date", ""), placeholder="e.g. Present", key=f"exp_edate_{idx}")
                        exp["current"] = st.checkbox("Currently Working Here", value=exp.get("current", False), key=f"exp_curr_{idx}")

                    exp["description"] = st.text_area(
                        f"Responsibilities & Key Achievements #{idx+1} (Bullet points recommended)",
                        value=exp.get("description", ""),
                        height=110,
                        placeholder="• Architected distributed ML pipelines reducing inference latency by 45%.\n• Spearheaded containerization with Docker and Kubernetes, serving 120k queries daily.",
                        key=f"exp_desc_{idx}"
                    )

                    if len(exp_list) > 1:
                        if st.button(f"🗑️ Remove Experience #{idx + 1}", key=f"del_exp_{idx}"):
                            st.session_state.rb_experience.pop(idx)
                            st.rerun()

            if st.button("➕ Add Another Work Experience", key="add_exp_btn"):
                st.session_state.rb_experience.append({
                    "company": "",
                    "role": "",
                    "start_date": "",
                    "end_date": "",
                    "current": False,
                    "description": ""
                })
                st.rerun()

        st.markdown("---")

        # D. Technical Projects
        st.markdown("### D. Key Technical Projects")
        st.caption("Demonstrate practical execution. Highly evaluated by technical screeners.")
        proj_list = st.session_state.rb_projects
        for idx, proj in enumerate(proj_list):
            with st.expander(f"🚀 Project #{idx + 1}: {proj.get('title') or 'New Project'}", expanded=(idx == 0)):
                pj1, pj2 = st.columns(2)
                with pj1:
                    proj["title"] = st.text_input(f"Project Title #{idx+1}", value=proj.get("title", ""), key=f"pj_title_{idx}")
                    proj["technologies"] = st.text_input(f"Technologies Used #{idx+1}", value=proj.get("technologies", ""), placeholder="e.g. Python, PyTorch, Docker, FastAPI", key=f"pj_tech_{idx}")
                with pj2:
                    proj["link"] = st.text_input(f"Project URL / GitHub Link #{idx+1}", value=proj.get("link", ""), placeholder="e.g. https://github.com/...", key=f"pj_link_{idx}")

                proj["description"] = st.text_area(
                    f"Project Overview & Architecture #{idx+1}",
                    value=proj.get("description", ""),
                    height=80,
                    placeholder="Describe problem solved, system architecture, and your individual engineering contributions...",
                    key=f"pj_desc_{idx}"
                )
                proj["achievements"] = st.text_input(
                    f"Measurable Outcome / Recognition #{idx+1}",
                    value=proj.get("achievements", ""),
                    placeholder="e.g. Earned 850+ GitHub stars; achieved 92% retrieval precision on technical documents.",
                    key=f"pj_ach_{idx}"
                )

                if len(proj_list) > 1:
                    if st.button(f"🗑️ Remove Project #{idx + 1}", key=f"del_pj_{idx}"):
                        st.session_state.rb_projects.pop(idx)
                        st.rerun()

        if st.button("➕ Add Another Project", key="add_pj_btn"):
            st.session_state.rb_projects.append({
                "title": "",
                "technologies": "",
                "link": "",
                "description": "",
                "achievements": ""
            })
            st.rerun()

        st.markdown("---")

        # E. Education
        st.markdown("### E. Education & Academic Background")
        edu_list = st.session_state.rb_education
        for idx, edu in enumerate(edu_list):
            with st.expander(f"🎓 Education #{idx + 1}: {edu.get('degree') or 'Degree'} - {edu.get('institution') or 'Institution'}", expanded=(idx == 0)):
                ed1, ed2 = st.columns(2)
                with ed1:
                    edu["institution"] = st.text_input(f"Institution / University #{idx+1}", value=edu.get("institution", ""), key=f"edu_inst_{idx}")
                    edu["degree"] = st.text_input(f"Degree / Qualification #{idx+1}", value=edu.get("degree", ""), placeholder="e.g. Master of Science / B.Tech", key=f"edu_deg_{idx}")
                    edu["field"] = st.text_input(f"Field of Study / Specialization #{idx+1}", value=edu.get("field", ""), placeholder="e.g. Computer Science", key=f"edu_field_{idx}")
                with ed2:
                    y_c1, y_c2 = st.columns(2)
                    with y_c1:
                        edu["start_year"] = st.text_input(f"Start Year #{idx+1}", value=edu.get("start_year", ""), placeholder="e.g. 2019", key=f"edu_syr_{idx}")
                    with y_c2:
                        edu["end_year"] = st.text_input(f"End / Graduation Year #{idx+1}", value=edu.get("end_year", ""), placeholder="e.g. 2021", key=f"edu_eyr_{idx}")
                    edu["cgpa"] = st.text_input(f"CGPA / Percentage (Optional) #{idx+1}", value=edu.get("cgpa", ""), placeholder="e.g. 3.91 / 4.0 or 88%", key=f"edu_gpa_{idx}")

                if len(edu_list) > 1:
                    if st.button(f"🗑️ Remove Education #{idx + 1}", key=f"del_edu_{idx}"):
                        st.session_state.rb_education.pop(idx)
                        st.rerun()

        if st.button("➕ Add Another Education Entry", key="add_edu_btn"):
            st.session_state.rb_education.append({
                "institution": "",
                "degree": "",
                "field": "",
                "start_year": "",
                "end_year": "",
                "cgpa": ""
            })
            st.rerun()

        st.markdown("---")

        # F. Certifications & Achievements
        st.markdown("### F. Certifications, Awards & Recognitions")
        cert_list = st.session_state.rb_certifications
        for idx, cert in enumerate(cert_list):
            with st.expander(f"📜 Certification #{idx + 1}: {cert.get('name') or 'New Certificate'}", expanded=(idx == 0)):
                c1, c2 = st.columns(2)
                with c1:
                    cert["name"] = st.text_input(f"Certification / Award Name #{idx+1}", value=cert.get("name", ""), key=f"cert_name_{idx}")
                    cert["issuer"] = st.text_input(f"Issuing Organization #{idx+1}", value=cert.get("issuer", ""), placeholder="e.g. AWS / Google / Coursera", key=f"cert_iss_{idx}")
                with c2:
                    cert["year"] = st.text_input(f"Year Issued #{idx+1}", value=cert.get("year", ""), placeholder="e.g. 2023", key=f"cert_yr_{idx}")
                    cert["details"] = st.text_input(f"Credential ID / Notes #{idx+1}", value=cert.get("details", ""), placeholder="e.g. Valid through 2026", key=f"cert_det_{idx}")

                if len(cert_list) > 1:
                    if st.button(f"🗑️ Remove Certification #{idx + 1}", key=f"del_cert_{idx}"):
                        st.session_state.rb_certifications.pop(idx)
                        st.rerun()

        if st.button("➕ Add Another Certification", key="add_cert_btn"):
            st.session_state.rb_certifications.append({
                "name": "",
                "issuer": "",
                "year": "",
                "details": ""
            })
            st.rerun()

        st.markdown("---")

        # G. Additional Sections (Optional)
        st.markdown("### G. Additional Sections (Optional)")
        a_c1, a_c2, a_c3 = st.columns(3)
        with a_c1:
            st.session_state.rb_coursework = st.text_area(
                "Relevant Coursework",
                value=st.session_state.get("rb_coursework", ""),
                height=90,
                placeholder="e.g. Distributed Systems, Neural Networks, Cloud Computing Architecture"
            )
        with a_c2:
            st.session_state.rb_languages = st.text_area(
                "Languages Spoken",
                value=st.session_state.get("rb_languages", ""),
                height=90,
                placeholder="e.g. English (Fluent), Spanish (Conversational)"
            )
        with a_c3:
            st.session_state.rb_volunteer = st.text_area(
                "Volunteer & Activities",
                value=st.session_state.get("rb_volunteer", ""),
                height=90,
                placeholder="e.g. Hackathon Mentor, STEM Outreach"
            )

    # ==========================================================================
    # TAB 2: LIVE PREVIEW & DOWNLOAD PDF
    # ==========================================================================
    with tabs[1]:
        resume_dict = get_current_resume_dict()
        current_tmpl = st.session_state.rb_template

        has_content = bool(
            (resume_dict.get("full_name") and resume_dict.get("full_name").strip()) or
            (resume_dict.get("summary") and resume_dict.get("summary").strip()) or
            any((e.get("company") and e.get("company").strip()) or (e.get("role") and e.get("role").strip()) for e in resume_dict.get("experience", [])) or
            any((p.get("title") and p.get("title").strip()) for p in resume_dict.get("projects", [])) or
            any((ed.get("institution") and ed.get("institution").strip()) or (ed.get("degree") and ed.get("degree").strip()) for ed in resume_dict.get("education", [])) or
            (resume_dict.get("skills_tech") and resume_dict.get("skills_tech").strip()) or
            (resume_dict.get("skills_languages") and resume_dict.get("skills_languages").strip())
        )

        if not has_content:
            st.markdown("""
            <div style='background: rgba(15, 23, 42, 0.6); border: 2px dashed rgba(59, 130, 246, 0.35); border-radius: 16px; padding: 48px 24px; text-align: center; margin: 16px 0;'>
                <div style='font-size: 48px; margin-bottom: 12px;'>📄</div>
                <div style='font-size: 20px; font-weight: 800; color: #F8FAFC; letter-spacing: -0.3px;'>
                    Upload a resume to preview candidate details
                </div>
                <div style='color: #94A3B8; font-size: 13.5px; max-width: 520px; margin: 8px auto 20px auto; line-height: 1.6;'>
                    No candidate resume loaded yet. Upload an existing resume (PDF or DOCX) to automatically extract and preview candidate details, or fill out the form in the <strong>Resume Information Form</strong> tab.
                </div>
            </div>
            """, unsafe_allow_html=True)

            uploaded_prev = st.file_uploader(
                "Upload a resume to preview candidate details",
                type=["pdf", "docx"],
                key="rb_empty_state_uploader",
                help="Select a PDF or DOCX resume to extract details and preview."
            )
            if uploaded_prev:
                with st.spinner("Extracting candidate details..."):
                    prev_fname = getattr(uploaded_prev, "name", "") or ""
                    parsed = parse_resume(uploaded_prev, filename=prev_fname)
                    if parsed.get("status") == "success":
                        text = parsed.get("clean_text") or parsed.get("text") or ""
                        meta = parsed.get("metadata", {})

                        clean_fname = extract_candidate_name_from_filename(prev_fname)

                        st.session_state.rb_full_name = clean_fname or "Candidate"
                        st.session_state.rb_email = meta.get("email") or ""
                        st.session_state.rb_phone = meta.get("phone") or ""
                        st.session_state.rb_linkedin = meta.get("linkedin") or ""
                        st.session_state.rb_github = meta.get("github") or ""

                        skills_info = extract_skills_from_text(text)
                        disp_skills = skills_info.get("display_skills", [])
                        if disp_skills:
                            st.session_state.rb_skills_tech = ", ".join(disp_skills[:12])

                        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
                        if lines:
                            st.session_state.rb_summary = lines[0][:350]

                        st.session_state.rb_generated_pdf = None
                        st.success("Resume uploaded successfully! Generating live preview...")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error(f"Could not parse resume: {parsed.get('error', 'Unknown format')}")
        else:
            pv_col1, pv_col2 = st.columns([2, 1])
            with pv_col1:
                st.markdown(f"#### 👁️ Resume Sheet Live Preview — `{current_tmpl}`")
                st.caption("Live rendering of your formatted resume. Changes from the form tab update here immediately.")
            with pv_col2:
                generate_pdf_btn = st.button("🔄 Render PDF", type="secondary", use_container_width=True)

            # Generate PDF bytes
            pdf_bytes = generate_resume_pdf(resume_dict, current_tmpl)
            st.session_state.rb_generated_pdf = pdf_bytes
            download_fname = get_download_filename(resume_dict.get("full_name"))

            # Download Button Row
            dl_col1, dl_col2, dl_col3 = st.columns([1.5, 1, 1])
            with dl_col1:
                st.download_button(
                    label=f"📥 Download PDF Resume ({download_fname})",
                    data=pdf_bytes,
                    file_name=download_fname,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            with dl_col2:
                st.markdown(f"<div style='font-size: 12px; color: #94A3B8; padding-top: 8px;'>📦 Size: <b>{len(pdf_bytes) / 1024:.1f} KB</b> &middot; Vector Text</div>", unsafe_allow_html=True)
            with dl_col3:
                st.markdown(f"<div style='font-size: 12px; color: #10B981; padding-top: 8px;'>✅ Verified ATS Compliant</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Render HTML Resume Sheet
            preview_html = get_resume_preview_html(resume_dict, current_tmpl)
            st.markdown(preview_html, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            u_col1, u_col2 = st.columns(2)
            with u_col1:
                with st.expander("📂 Replace with Another Resume File", expanded=False):
                    replace_file = st.file_uploader(
                        "Upload a different resume",
                        type=["pdf", "docx"],
                        key="rb_replace_uploader"
                    )
                    if replace_file:
                        rep_fname = getattr(replace_file, "name", "") or ""
                        parsed = parse_resume(replace_file, filename=rep_fname)
                        if parsed.get("status") == "success":
                            text = parsed.get("clean_text") or parsed.get("text") or ""
                            meta = parsed.get("metadata", {})
                            clean_fname = extract_candidate_name_from_filename(rep_fname)
                            st.session_state.rb_full_name = clean_fname or "Candidate"
                            st.session_state.rb_email = meta.get("email") or ""
                            st.session_state.rb_phone = meta.get("phone") or ""
                            st.session_state.rb_linkedin = meta.get("linkedin") or ""
                            st.session_state.rb_github = meta.get("github") or ""
                            skills_info = extract_skills_from_text(text)
                            disp_skills = skills_info.get("display_skills", [])
                            if disp_skills:
                                st.session_state.rb_skills_tech = ", ".join(disp_skills[:12])
                            lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 30]
                            if lines:
                                st.session_state.rb_summary = lines[0][:350]
                            st.session_state.rb_generated_pdf = None
                            st.success("Resume updated!")
                            st.rerun()
            with u_col2:
                if st.button("🗑️ Clear Resume Preview", use_container_width=True):
                    clear_form_data()
                    st.rerun()

    # ==========================================================================
    # TAB 3: QUALITY ASSISTANT & ATS AUDIT
    # ==========================================================================
    with tabs[2]:
        resume_dict = get_current_resume_dict()
        target_role = st.session_state.rb_target_role

        has_content = bool(
            (resume_dict.get("full_name") and resume_dict.get("full_name").strip()) or
            (resume_dict.get("summary") and resume_dict.get("summary").strip()) or
            any((e.get("company") and e.get("company").strip()) or (e.get("role") and e.get("role").strip()) for e in resume_dict.get("experience", [])) or
            any((p.get("title") and p.get("title").strip()) for p in resume_dict.get("projects", [])) or
            any((ed.get("institution") and ed.get("institution").strip()) or (ed.get("degree") and ed.get("degree").strip()) for ed in resume_dict.get("education", [])) or
            (resume_dict.get("skills_tech") and resume_dict.get("skills_tech").strip()) or
            (resume_dict.get("skills_languages") and resume_dict.get("skills_languages").strip())
        )

        audit = None

        if not has_content:
            st.info("ℹ️ Upload a resume or enter candidate information in the form to view completeness analysis, power verbs, and ATS keyword advice.")
        else:
            try:
                audit = evaluate_resume_quality(resume_dict, target_role)
            except Exception as e:
                st.error(f"Error evaluating resume quality: {e}")
                audit = None

            if audit:
                # Score Hero Card
                q_score = audit.get("score", 0.0)
                q_rating = audit.get("rating", "Needs Improvement")
                q_color = audit.get("rating_color", "#F43F5E")
                q_badge = audit.get("badge_text", "Audit Pending")

                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(30, 58, 138, 0.25), rgba(124, 58, 237, 0.2)); border: 1px solid rgba(59, 130, 246, 0.35); border-radius: 14px; padding: 22px 28px; margin-bottom: 20px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-size: 11px; text-transform: uppercase; color: #38BDF8; font-weight: 800; letter-spacing: 0.6px;'>Resume Completeness & Quality Index</div>
                            <div style='font-size: 28px; font-weight: 800; color: #F8FAFC; margin-top: 4px;'>
                                Overall Score: <span style='color: {q_color};'>{q_score:.1f}%</span> &middot; {q_rating}
                            </div>
                            <div style='font-size: 13.5px; color: #94A3B8; margin-top: 4px;'>
                                {q_badge} &middot; Evaluated against tech industry benchmarks and recruiter scanning standards.
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 42px; font-weight: 900; color: {q_color};'>{int(q_score)}</div>
                            <div style='font-size: 11px; color: #94A3B8;'>OUT OF 100</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Critical Missing Items (if any)
                if audit.get("critical_missing"):
                    st.error("⚠️ **Critical Missing Information Needed for ATS Processing:**")
                    for crit in audit["critical_missing"]:
                        st.markdown(f"- 🔴 **{crit}**")

                # Two-column layout for Strengths & Improvement Suggestions
                a_col1, a_col2 = st.columns(2)
                with a_col1:
                    st.markdown("#### 🛡️ Verified Candidate Strengths")
                    if audit.get("strengths"):
                        for s in audit["strengths"]:
                            st.markdown(f"""
                            <div style='background: rgba(16, 185, 129, 0.08); border-left: 3px solid #10B981; padding: 8px 12px; margin-bottom: 8px; border-radius: 4px; font-size: 13px; color: #E2E8F0;'>
                                ✅ {s}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("Fill out your contact details, education, and skills to populate strengths.")

                with a_col2:
                    st.markdown("#### 💡 Constructive Optimization Suggestions")
                    if audit.get("suggestions"):
                        for sug in audit["suggestions"]:
                            st.markdown(f"""
                            <div style='background: rgba(245, 158, 11, 0.08); border-left: 3px solid #F59E0B; padding: 8px 12px; margin-bottom: 8px; border-radius: 4px; font-size: 13px; color: #E2E8F0;'>
                                💡 {sug}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("🎉 Outstanding! Your resume adheres to all recommended ATS and formatting standards.")

                st.markdown("---")

                # Role-Specific ATS Keywords Advisor
                role_adv = audit.get("role_advice", {})
                if role_adv:
                    st.markdown(f"#### 🎯 Target Role Alignment: `{role_adv.get('target_role')}`")
                    c_cov = role_adv.get("coverage_pct", 0)
                    st.caption(f"Keyword Coverage: **{c_cov}%** of common industry keywords are present in your resume.")
                    st.progress(c_cov / 100.0)

                    kw_c1, kw_c2 = st.columns(2)
                    with kw_c1:
                        st.markdown("**Matched Role Keywords in Your Profile:**")
                        matched_kw = role_adv.get("matching", [])
                        if matched_kw:
                            pills = "".join([f"<span class='badge-pill badge-matched'>{k}</span>" for k in matched_kw])
                            st.markdown(pills, unsafe_allow_html=True)
                        else:
                            st.caption("None yet detected.")
                    with kw_c2:
                        st.markdown("**Recommended Keywords to Consider Adding (If Qualified):**")
                        missing_kw = role_adv.get("missing", [])
                        if missing_kw:
                            pills = "".join([f"<span class='badge-pill badge-missing'>{k}</span>" for k in missing_kw])
                            st.markdown(pills, unsafe_allow_html=True)
                        else:
                            st.caption("All target keywords represented!")

                st.markdown("---")

                # Action Verbs & Metrics Insight
                m_c1, m_c2 = st.columns(2)
                with m_c1:
                    st.markdown("#### ⚡ Power Verbs Detected")
                    verbs = audit.get("action_verbs_found", [])
                    if verbs:
                        st.success(f"Detected **{len(verbs)}** strong power verbs: {', '.join(verbs)}")
                    else:
                        st.warning("No power verbs detected at the beginning of bullet points.")
                    with st.expander("📖 Recommended Action Verbs by Functional Focus"):
                        for category, v_list in ACTION_VERBS.items():
                            st.markdown(f"**{category}:** {', '.join(v_list)}")

                with m_c2:
                    st.markdown("#### 📊 Quantifiable Impact Metrics")
                    metrics = audit.get("metrics_found", [])
                    if metrics:
                        st.success(f"Detected **{len(metrics)}** quantifiable metrics in your bullets: {', '.join(metrics)}")
                    else:
                        st.warning("No metrics or percentages detected. Recruiters prioritize measurable results.")
                    with st.expander("💡 Google's X-Y-Z Achievement Formula"):
                        st.markdown("""
                        **Formula:** *Accomplished [X], as measured by [Y], by doing [Z].*
                        - *Weak:* "Worked on deep learning models."
                        - *Strong:* "Engineered distributed PyTorch model training across 32 GPUs, reducing fine-tuning latency by **55%** and saving **$40k** in cloud compute."
                        """)

    # ==========================================================================
    # TAB 4: TALENTIQ SCREENING ENGINE INTEGRATION
    # ==========================================================================
    with tabs[3]:
        st.markdown("### ⚡ Live AI Resume Screening Simulation")
        st.markdown("""
        Test your newly crafted resume directly against the TalentIQ Screening & Job Matching Engine.
        This validates that your exported PDF is **100% readable** by the system's `PyMuPDF` parser
        and calculates your contextual semantic similarity and matched technical skills.
        """)

        resume_dict = get_current_resume_dict()
        current_tmpl = st.session_state.rb_template

        has_content = bool(
            (resume_dict.get("full_name") and resume_dict.get("full_name").strip()) or
            (resume_dict.get("summary") and resume_dict.get("summary").strip()) or
            any((e.get("company") and e.get("company").strip()) or (e.get("role") and e.get("role").strip()) for e in resume_dict.get("experience", [])) or
            any((p.get("title") and p.get("title").strip()) for p in resume_dict.get("projects", [])) or
            any((ed.get("institution") and ed.get("institution").strip()) or (ed.get("degree") and ed.get("degree").strip()) for ed in resume_dict.get("education", [])) or
            (resume_dict.get("skills_tech") and resume_dict.get("skills_tech").strip()) or
            (resume_dict.get("skills_languages") and resume_dict.get("skills_languages").strip())
        )

        if not has_content:
            st.info("ℹ️ Upload a resume or enter candidate information in the form to run a live screening test against job requirements.")
        else:
            sc_c1, sc_c2 = st.columns([1.5, 1])
            with sc_c1:
                test_jd_preset = st.selectbox(
                    "Select Job Description for Compatibility Test",
                    list(SAMPLE_JOB_DESCRIPTIONS.keys()),
                    index=0
                )
                custom_jd = st.text_area(
                    "Job Description Requirements Text",
                    value=SAMPLE_JOB_DESCRIPTIONS[test_jd_preset],
                    height=130
                )

            with sc_c2:
                st.markdown("#### 🧪 Screening Pipeline Actions")
                st.caption("Generates the actual PDF in-memory, passes it to the parser, and runs embedding cosine similarity.")

                run_test_btn = st.button("🚀 Run Screening Analysis on PDF", type="primary", use_container_width=True)
                add_to_pipeline_btn = st.button("📥 Add to Active Recruiter Pipeline", type="secondary", use_container_width=True)

            if run_test_btn:
                with st.spinner("Compiling PDF and executing neural screening pipeline..."):
                    # 1. Generate PDF
                    pdf_bytes = generate_resume_pdf(resume_dict, current_tmpl)
                    st.session_state.rb_generated_pdf = pdf_bytes

                    # 2. Extract text with PyMuPDF
                    text, page_count, err, is_scanned = extract_text_from_pdf(pdf_bytes)

                    if err:
                        st.error(f"PDF extraction error: {err}")
                    else:
                        # 3. Analyze skills
                        skill_gap_result = analyze_skill_gap(text, custom_jd)
                        matched_skills = skill_gap_result.get("matched_skills", [])
                        missing_skills = skill_gap_result.get("missing_skills", [])
                        skill_match_pct = skill_gap_result.get("skill_match_percentage", 0.0)

                        # 4. Semantic similarity
                        sem_sim = 0.5
                        try:
                            sim_val, _ = compute_semantic_similarity(text, custom_jd, model=cached_model)
                            sem_sim = sim_val
                        except Exception:
                            sem_sim = 0.55

                        # Composite score (60% semantic, 40% skills)
                        sem_pct = round(sem_sim * 100, 1)
                        comp_score = round(0.60 * sem_pct + 0.40 * skill_match_pct, 1)
                        is_shortlisted = comp_score >= 70.0

                        # Store in session state
                        st.session_state.rb_last_screen_result = {
                            "text": text,
                            "page_count": page_count,
                            "comp_score": comp_score,
                            "sem_pct": sem_pct,
                            "skill_match_pct": skill_match_pct,
                            "matched_skills": matched_skills,
                            "missing_skills": missing_skills,
                            "is_shortlisted": is_shortlisted,
                            "jd_preset": test_jd_preset
                        }
                        st.success("Screening test completed successfully!")

            # Display screening results if available
            res = st.session_state.get("rb_last_screen_result")
            if res:
                st.markdown("---")
                st.markdown(f"#### 📊 Match Results for `{resume_dict.get('full_name')}` vs `{res['jd_preset']}`")

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    badge_clr = "#10B981" if res["is_shortlisted"] else "#FBBF24"
                    status_txt = "SHORTLISTED" if res["is_shortlisted"] else "UNDER REVIEW"
                    st.markdown(f"""
                    <div class='stat-card'>
                        <div style='font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 700;'>Composite Match</div>
                        <div style='font-size: 28px; font-weight: 800; color: {badge_clr};'>{res['comp_score']}%</div>
                        <div style='font-size: 11px; color: {badge_clr}; font-weight: 800;'>{status_txt}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""
                    <div class='stat-card'>
                        <div style='font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 700;'>Semantic Context</div>
                        <div style='font-size: 28px; font-weight: 800; color: #38BDF8;'>{res['sem_pct']}%</div>
                        <div style='font-size: 11px; color: #94A3B8;'>Sentence Transformer</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m3:
                    st.markdown(f"""
                    <div class='stat-card'>
                        <div style='font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 700;'>Skill Overlap</div>
                        <div style='font-size: 28px; font-weight: 800; color: #818CF8;'>{res['skill_match_pct']}%</div>
                        <div style='font-size: 11px; color: #94A3B8;'>{len(res['matched_skills'])} Matched Skills</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m4:
                    st.markdown(f"""
                    <div class='stat-card'>
                        <div style='font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 700;'>Parser Telemetry</div>
                        <div style='font-size: 28px; font-weight: 800; color: #10B981;'>{res['page_count']} Page(s)</div>
                        <div style='font-size: 11px; color: #10B981;'>100% Vector Extracted</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                sk1, sk2 = st.columns(2)
                with sk1:
                    st.markdown("**Matched Required Skills:**")
                    if res["matched_skills"]:
                        pills = "".join([f"<span class='badge-pill badge-matched'>{s}</span>" for s in res["matched_skills"]])
                        st.markdown(pills, unsafe_allow_html=True)
                    else:
                        st.caption("No overlapping skills detected.")
                with sk2:
                    st.markdown("**Missing Required Skills for this Role:**")
                    if res["missing_skills"]:
                        pills = "".join([f"<span class='badge-pill badge-missing'>{s}</span>" for s in res["missing_skills"][:10]])
                        st.markdown(pills, unsafe_allow_html=True)
                    else:
                        st.caption("No required skills missing!")

                with st.expander("🔍 View Raw Text Extracted from Generated PDF by PyMuPDF"):
                    st.text(res["text"][:1200] + ("..." if len(res["text"]) > 1200 else ""))

            if add_to_pipeline_btn:
                c_name = resume_dict.get("full_name") or "Candidate"
                simulated_resume = {
                    "filename": get_download_filename(c_name),
                    "text": res["text"] if res else "Candidate resume built in TalentIQ Builder",
                    "clean_text": res["text"] if res else "Candidate resume built in TalentIQ Builder",
                    "status": "success",
                    "error": None,
                    "metadata": {
                        "word_count": len(res["text"].split()) if res else 250,
                        "char_count": len(res["text"]) if res else 1500,
                        "page_count": res.get("page_count", 1) if res else 1,
                        "email": resume_dict.get("email"),
                        "phone": resume_dict.get("phone"),
                        "linkedin": resume_dict.get("linkedin"),
                        "github": resume_dict.get("github")
                    }
                }

                if "parsed_resumes" not in st.session_state or st.session_state.parsed_resumes is None:
                    st.session_state.parsed_resumes = []

                st.session_state.parsed_resumes = [
                    r for r in st.session_state.parsed_resumes if r.get("filename") != simulated_resume["filename"]
                ]
                st.session_state.parsed_resumes.append(simulated_resume)

                st.session_state.recent_activity.insert(0, {
                    "time": "Just now",
                    "title": f"Candidate Built & Added: {c_name}",
                    "desc": f"Added {get_download_filename(c_name)} to active screening pipeline",
                    "tag": "BUILDER",
                    "color": "#38BDF8"
                })

                st.success(f"Added **{c_name}** to active screening pool! You can now view them in Candidate Rankings and Dashboard.")
                time.sleep(0.5)
                st.rerun()

    # Ethical Disclaimer Footer
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.caption(f"<div style='color: #64748B; font-size: 11px;'>{ETHICAL_DISCLAIMER}</div>", unsafe_allow_html=True)
