"""
AI Resume Screening and Job Matching System - HTML/CSS Resume Templates for Live Preview.
Renders responsive, high-fidelity resume sheets inside Streamlit matching:
1. Modern Professional
2. Minimal ATS-Friendly
3. Technical / Software Developer
"""

import html
import re
from typing import Dict, Any, List


def escape(val: Any) -> str:
    """Safely escapes HTML special characters."""
    if not val:
        return ""
    return html.escape(str(val).strip())


def safe_url(url: Any) -> str:
    """Ensures a URL is an http(s) link to prevent javascript: or data: URIs."""
    if not url:
        return ""
    u = str(url).strip()
    if not u:
        return ""
    if u.lower().startswith(("http://", "https://")):
        return html.escape(u, quote=True)
    if not any(u.lower().startswith(p) for p in ("javascript:", "data:", "vbscript:", "file:")):
        return f"https://{html.escape(u, quote=True)}"
    return "#"


def sanitize_link_text(url: Any) -> str:
    """Sanitizes link text to prevent dangerous protocols like javascript: or data: in text."""
    if not url:
        return ""
    u = str(url).strip()
    if any(u.lower().startswith(p) for p in ("javascript:", "data:", "vbscript:", "file:")):
        return ""
    return escape(u)


def _clean_html_for_markdown(html_str: str) -> str:
    """
    Normalizes HTML for rendering in Streamlit markdown.
    CommonMark treats any line indented with 4 or more spaces following a blank line
    as an indented code block (<pre><code>...</code></pre>), causing HTML tags like
    <div>, <strong>, <ul>, and <li> to be rendered as literal visible source code.
    By trimming leading whitespace from each line and eliminating blank-line-plus-indent
    patterns, we ensure the entire HTML document is parsed strictly as raw HTML.
    """
    if not html_str:
        return ""
    lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    return "\n".join(lines)


def _format_bullets_html(text: str) -> str:
    """Converts multiline or bulleted text into clean HTML <li> elements."""
    if not text:
        return ""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        clean = re.sub(r"^[\-\*\•\d+\.]\s*", "", line).strip()
        if clean:
            lines.append(f"<li style='margin-bottom: 4px; line-height: 1.5;'>{escape(clean)}</li>")
    if lines:
        return f"<ul style='margin: 4px 0 8px 18px; padding: 0;'>{''.join(lines)}</ul>"
    return ""


# ==============================================================================
# TEMPLATE 1: MODERN PROFESSIONAL (HTML)
# ==============================================================================
def render_modern_professional_html(resume_data: Dict[str, Any]) -> str:
    name = escape(resume_data.get("full_name") or "Candidate Name")
    headline = escape(resume_data.get("headline") or "")
    email = escape(resume_data.get("email") or "")
    phone = escape(resume_data.get("phone") or "")
    location = escape(resume_data.get("location") or "")
    linkedin = escape(resume_data.get("linkedin") or "")
    github = escape(resume_data.get("github") or "")
    portfolio = escape(resume_data.get("portfolio") or "")
    summary = escape(resume_data.get("summary") or "")

    # Contact row
    contact_parts = []
    if email:
        contact_parts.append(f"<a href='mailto:{email}' style='color: #1E3A8A; text-decoration: none;'>📧 {email}</a>")
    if phone:
        contact_parts.append(f"<span>📞 {phone}</span>")
    if location:
        contact_parts.append(f"<span>📍 {location}</span>")
    if linkedin:
        contact_parts.append(f"<a href='{safe_url(linkedin)}' target='_blank' style='color: #2563EB; text-decoration: none;'>🔗 LinkedIn</a>")
    if github:
        contact_parts.append(f"<a href='{safe_url(github)}' target='_blank' style='color: #2563EB; text-decoration: none;'>🐙 GitHub</a>")
    if portfolio:
        contact_parts.append(f"<a href='{safe_url(portfolio)}' target='_blank' style='color: #2563EB; text-decoration: none;'>🌐 Portfolio</a>")

    contact_html = " &bull; ".join(contact_parts)

    def section_header(title: str) -> str:
        return f"""
        <div style='margin-top: 18px; margin-bottom: 6px;'>
            <div style='font-size: 13px; font-weight: 800; color: #1E3A8A; letter-spacing: 0.5px; text-transform: uppercase;'>{title}</div>
            <div style='height: 2px; background: linear-gradient(90deg, #1E3A8A, #3B82F6, transparent); margin-top: 3px;'></div>
        </div>
        """

    # Skills
    skills_html = ""
    skills_tech = escape(resume_data.get("skills_tech", ""))
    skills_lang = escape(resume_data.get("skills_languages", ""))
    skills_tools = escape(resume_data.get("skills_tools", ""))
    skills_soft = escape(resume_data.get("skills_soft", ""))

    if skills_tech or skills_lang or skills_tools or skills_soft:
        rows = []
        if skills_lang:
            rows.append(f"<div><strong style='color: #0F172A;'>Languages:</strong> {skills_lang}</div>")
        if skills_tech:
            rows.append(f"<div><strong style='color: #0F172A;'>Technical Skills:</strong> {skills_tech}</div>")
        if skills_tools:
            rows.append(f"<div><strong style='color: #0F172A;'>Frameworks & Tools:</strong> {skills_tools}</div>")
        if skills_soft:
            rows.append(f"<div><strong style='color: #0F172A;'>Soft Skills:</strong> {skills_soft}</div>")
        skills_html = section_header("Skills & Competencies") + f"<div style='font-size: 12.5px; color: #334155; line-height: 1.6;'>{''.join(rows)}</div>"

    # Work Experience
    exp_html = ""
    if not resume_data.get("is_fresher", False):
        exp_entries = resume_data.get("experience", [])
        exp_blocks = []
        for e in exp_entries:
            comp = escape(e.get("company", ""))
            role = escape(e.get("role", ""))
            start = escape(e.get("start_date", ""))
            end = "Present" if e.get("current") else escape(e.get("end_date", ""))
            dates = f"{start} – {end}" if start or end else ""
            desc = _format_bullets_html(e.get("description", ""))
            if not comp and not role:
                continue
            exp_blocks.append(f"""
            <div style='margin-bottom: 12px;'>
                <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                    <span style='font-size: 13.5px; font-weight: 700; color: #0F172A;'>{role}</span>
                    <span style='font-size: 12px; color: #64748B;'>{dates}</span>
                </div>
                <div style='font-size: 12.5px; font-style: italic; color: #475569; margin-bottom: 3px;'>{comp}</div>
                <div style='font-size: 12.5px; color: #334155;'>{desc}</div>
            </div>
            """)
        if exp_blocks:
            exp_html = section_header("Work Experience") + "".join(exp_blocks)

    # Projects
    proj_html = ""
    proj_entries = resume_data.get("projects", [])
    proj_blocks = []
    for p in proj_entries:
        title = escape(p.get("title", ""))
        tech = escape(p.get("technologies", ""))
        link = sanitize_link_text(p.get("link", ""))
        desc = _format_bullets_html(p.get("description", ""))
        achieve = _format_bullets_html(p.get("achievements", ""))
        if not title:
            continue
        link_tag = f"<a href='{safe_url(link)}' target='_blank' style='font-size: 11.5px; color: #2563EB; text-decoration: none;'>🔗 View Project</a>" if link else ""
        tech_badge = f"<span style='font-size: 11.5px; font-style: italic; color: #475569;'> | {tech}</span>" if tech else ""
        proj_blocks.append(f"""
        <div style='margin-bottom: 12px;'>
            <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                <div>
                    <span style='font-size: 13.5px; font-weight: 700; color: #0F172A;'>{title}</span>
                    {tech_badge}
                </div>
                <div>{link_tag}</div>
            </div>
            <div style='font-size: 12.5px; color: #334155; margin-top: 2px;'>{desc}{achieve}</div>
        </div>
        """)
    if proj_blocks:
        proj_html = section_header("Key Projects") + "".join(proj_blocks)

    # Education
    edu_html = ""
    edu_entries = resume_data.get("education", [])
    edu_blocks = []
    for ed in edu_entries:
        inst = escape(ed.get("institution", ""))
        deg = escape(ed.get("degree", ""))
        field = escape(ed.get("field", ""))
        s_yr = escape(ed.get("start_year", ""))
        e_yr = escape(ed.get("end_year", ""))
        cgpa = escape(ed.get("cgpa", ""))
        dates = f"{s_yr} – {e_yr}" if s_yr and e_yr else (e_yr or s_yr)
        deg_field = f"{deg} in {field}" if deg and field else (deg or field)
        if not inst and not deg:
            continue
        cgpa_str = f" &bull; <strong>CGPA:</strong> {cgpa}" if cgpa else ""
        edu_blocks.append(f"""
        <div style='margin-bottom: 10px;'>
            <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                <span style='font-size: 13px; font-weight: 700; color: #0F172A;'>{deg_field}</span>
                <span style='font-size: 12px; color: #64748B;'>{dates}</span>
            </div>
            <div style='font-size: 12.5px; color: #475569;'>{inst}{cgpa_str}</div>
        </div>
        """)
    if edu_blocks:
        edu_html = section_header("Education") + "".join(edu_blocks)

    # Certifications
    cert_html = ""
    cert_entries = resume_data.get("certifications", [])
    cert_items = []
    for c in cert_entries:
        c_name = escape(c.get("name", ""))
        c_iss = escape(c.get("issuer", ""))
        c_yr = escape(c.get("year", ""))
        c_det = escape(c.get("details", ""))
        if not c_name:
            continue
        line = f"<strong>{c_name}</strong>"
        if c_iss:
            line += f" — {c_iss}"
        if c_yr:
            line += f" ({c_yr})"
        if c_det:
            line += f": {c_det}"
        cert_items.append(f"<li style='margin-bottom: 3px;'>{line}</li>")
    if cert_items:
        cert_html = section_header("Certifications & Achievements") + f"<ul style='margin: 4px 0 8px 18px; padding: 0; font-size: 12.5px; color: #334155;'>{''.join(cert_items)}</ul>"

    # Additional sections
    add_html = ""
    add_dict = resume_data.get("additional_sections", {})
    if add_dict:
        for sec_name, sec_content in add_dict.items():
            if sec_content and sec_content.strip():
                bullets = _format_bullets_html(sec_content)
                add_html += section_header(escape(sec_name)) + f"<div style='font-size: 12.5px; color: #334155;'>{bullets}</div>"

    return f"""
    <div style='background: #FFFFFF; color: #0F172A; border-radius: 8px; padding: 36px 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; border: 1px solid #E2E8F0;'>
        <div style='border-bottom: 2px solid #CBD5E1; padding-bottom: 14px;'>
            <div style='font-size: 26px; font-weight: 800; color: #1E3A8A; letter-spacing: -0.5px;'>{name}</div>
            {f"<div style='font-size: 14px; font-weight: 700; color: #2563EB; margin-top: 3px;'>{headline}</div>" if headline else ""}
            <div style='font-size: 12px; color: #475569; margin-top: 6px; line-height: 1.6;'>{contact_html}</div>
        </div>

        {f"{section_header('Professional Summary')}<div style='font-size: 12.8px; color: #334155; line-height: 1.6;'>{summary}</div>" if summary else ""}
        {skills_html}
        {exp_html}
        {proj_html}
        {edu_html}
        {cert_html}
        {add_html}
    </div>
    """


# ==============================================================================
# TEMPLATE 2: MINIMAL ATS-FRIENDLY (HTML)
# ==============================================================================
def render_minimal_ats_html(resume_data: Dict[str, Any]) -> str:
    name = escape(resume_data.get("full_name") or "Candidate Name")
    headline = escape(resume_data.get("headline") or "")
    email = escape(resume_data.get("email") or "")
    phone = escape(resume_data.get("phone") or "")
    location = escape(resume_data.get("location") or "")
    linkedin = sanitize_link_text(resume_data.get("linkedin") or "")
    github = sanitize_link_text(resume_data.get("github") or "")
    portfolio = sanitize_link_text(resume_data.get("portfolio") or "")
    summary = escape(resume_data.get("summary") or "")

    contact_parts = [p for p in [email, phone, location, linkedin, github, portfolio] if p]
    contact_str = " | ".join(contact_parts)

    def section_header(title: str) -> str:
        return f"""
        <div style='margin-top: 16px; margin-bottom: 4px;'>
            <div style='font-size: 12px; font-weight: 800; color: #000000; text-transform: uppercase; letter-spacing: 0.5px;'>{title}</div>
            <hr style='border: none; border-top: 1px solid #4B5563; margin: 2px 0 6px 0;' />
        </div>
        """

    # Skills
    skills_html = ""
    skills_tech = escape(resume_data.get("skills_tech", ""))
    skills_lang = escape(resume_data.get("skills_languages", ""))
    skills_tools = escape(resume_data.get("skills_tools", ""))
    skills_soft = escape(resume_data.get("skills_soft", ""))

    if skills_tech or skills_lang or skills_tools or skills_soft:
        rows = []
        if skills_lang:
            rows.append(f"<div><strong>Programming Languages:</strong> {skills_lang}</div>")
        if skills_tech:
            rows.append(f"<div><strong>Technologies:</strong> {skills_tech}</div>")
        if skills_tools:
            rows.append(f"<div><strong>Frameworks & Tools:</strong> {skills_tools}</div>")
        if skills_soft:
            rows.append(f"<div><strong>Core Competencies:</strong> {skills_soft}</div>")
        skills_html = section_header("Technical Skills") + f"<div style='font-size: 12px; color: #1F2937; line-height: 1.5;'>{''.join(rows)}</div>"

    # Experience
    exp_html = ""
    if not resume_data.get("is_fresher", False):
        exp_entries = resume_data.get("experience", [])
        exp_blocks = []
        for e in exp_entries:
            comp = escape(e.get("company", ""))
            role = escape(e.get("role", ""))
            start = escape(e.get("start_date", ""))
            end = "Present" if e.get("current") else escape(e.get("end_date", ""))
            dates = f"{start} – {end}" if start or end else ""
            desc = _format_bullets_html(e.get("description", ""))
            if not comp and not role:
                continue
            exp_blocks.append(f"""
            <div style='margin-bottom: 10px;'>
                <div style='display: flex; justify-content: space-between;'>
                    <strong style='font-size: 12.5px; color: #000000;'>{role}, {comp}</strong>
                    <span style='font-size: 12px; color: #000000;'>{dates}</span>
                </div>
                <div style='font-size: 12px; color: #1F2937;'>{desc}</div>
            </div>
            """)
        if exp_blocks:
            exp_html = section_header("Professional Experience") + "".join(exp_blocks)

    # Projects
    proj_html = ""
    proj_entries = resume_data.get("projects", [])
    proj_blocks = []
    for p in proj_entries:
        title = escape(p.get("title", ""))
        tech = escape(p.get("technologies", ""))
        link = sanitize_link_text(p.get("link", ""))
        desc = _format_bullets_html(p.get("description", ""))
        achieve = _format_bullets_html(p.get("achievements", ""))
        if not title:
            continue
        tech_str = f" | <em>{tech}</em>" if tech else ""
        link_str = f"<span style='font-size: 11.5px;'>{link}</span>" if link else ""
        proj_blocks.append(f"""
        <div style='margin-bottom: 10px;'>
            <div style='display: flex; justify-content: space-between;'>
                <strong style='font-size: 12.5px; color: #000000;'>{title}{tech_str}</strong>
                {link_str}
            </div>
            <div style='font-size: 12px; color: #1F2937;'>{desc}{achieve}</div>
        </div>
        """)
    if proj_blocks:
        proj_html = section_header("Projects") + "".join(proj_blocks)

    # Education
    edu_html = ""
    edu_entries = resume_data.get("education", [])
    edu_blocks = []
    for ed in edu_entries:
        inst = escape(ed.get("institution", ""))
        deg = escape(ed.get("degree", ""))
        field = escape(ed.get("field", ""))
        s_yr = escape(ed.get("start_year", ""))
        e_yr = escape(ed.get("end_year", ""))
        cgpa = escape(ed.get("cgpa", ""))
        dates = f"{s_yr} – {e_yr}" if s_yr and e_yr else (e_yr or s_yr)
        deg_field = f"{deg} in {field}" if deg and field else (deg or field)
        if not inst and not deg:
            continue
        gpa_str = f" (GPA: {cgpa})" if cgpa else ""
        edu_blocks.append(f"""
        <div style='display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;'>
            <span><strong>{deg_field}</strong>, {inst}{gpa_str}</span>
            <span>{dates}</span>
        </div>
        """)
    if edu_blocks:
        edu_html = section_header("Education") + "".join(edu_blocks)

    # Certifications
    cert_html = ""
    cert_entries = resume_data.get("certifications", [])
    cert_items = []
    for c in cert_entries:
        c_name = escape(c.get("name", ""))
        c_iss = escape(c.get("issuer", ""))
        c_yr = escape(c.get("year", ""))
        if not c_name:
            continue
        line = f"<strong>{c_name}</strong>"
        if c_iss:
            line += f" – {c_iss}"
        if c_yr:
            line += f" ({c_yr})"
        cert_items.append(f"<li>{line}</li>")
    if cert_items:
        cert_html = section_header("Certifications & Awards") + f"<ul style='margin: 4px 0 8px 18px; padding: 0; font-size: 12px; color: #1F2937;'>{''.join(cert_items)}</ul>"

    return f"""
    <div style='background: #FFFFFF; color: #000000; border-radius: 4px; padding: 36px 40px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; line-height: 1.4; border: 1px solid #D1D5DB;'>
        <div style='text-align: center; margin-bottom: 12px;'>
            <div style='font-size: 24px; font-weight: 800; letter-spacing: 0.5px;'>{name.upper()}</div>
            {f"<div style='font-size: 13px; font-weight: 700; color: #1F2937; margin-top: 2px;'>{headline}</div>" if headline else ""}
            <div style='font-size: 11.5px; color: #374151; margin-top: 4px;'>{contact_str}</div>
        </div>

        {f"{section_header('Professional Summary')}<div style='font-size: 12px; color: #1F2937; text-align: justify;'>{summary}</div>" if summary else ""}
        {skills_html}
        {exp_html}
        {proj_html}
        {edu_html}
        {cert_html}
    </div>
    """


# ==============================================================================
# TEMPLATE 3: TECHNICAL / SOFTWARE DEVELOPER (HTML)
# ==============================================================================
def render_technical_developer_html(resume_data: Dict[str, Any]) -> str:
    name = escape(resume_data.get("full_name") or "Candidate Name")
    headline = escape(resume_data.get("headline") or "Software Engineer")
    email = escape(resume_data.get("email") or "")
    phone = escape(resume_data.get("phone") or "")
    location = escape(resume_data.get("location") or "")
    linkedin = escape(resume_data.get("linkedin") or "")
    github = escape(resume_data.get("github") or "")
    portfolio = escape(resume_data.get("portfolio") or "")
    summary = escape(resume_data.get("summary") or "")

    contact_parts = []
    if email:
        contact_parts.append(f"<a href='mailto:{email}' style='color: #0284C7; text-decoration: none;'>{email}</a>")
    if phone:
        contact_parts.append(f"<span>{phone}</span>")
    if location:
        contact_parts.append(f"<span>{location}</span>")
    if github:
        contact_parts.append(f"<a href='{safe_url(github)}' target='_blank' style='color: #0284C7; font-weight: 600;'>github</a>")
    if portfolio:
        contact_parts.append(f"<a href='{safe_url(portfolio)}' target='_blank' style='color: #0284C7; font-weight: 600;'>portfolio</a>")
    if linkedin:
        contact_parts.append(f"<a href='{safe_url(linkedin)}' target='_blank' style='color: #0284C7; font-weight: 600;'>linkedin</a>")

    contact_html = " &middot; ".join(contact_parts)

    def section_header(title: str) -> str:
        return f"""
        <div style='margin-top: 18px; margin-bottom: 6px;'>
            <div style='font-size: 13px; font-weight: 800; color: #4338CA; letter-spacing: 0.5px;'>// {title.upper()}</div>
            <div style='height: 1.5px; background: #4338CA; margin-top: 3px;'></div>
        </div>
        """

    # Technical Skills
    skills_html = ""
    skills_tech = escape(resume_data.get("skills_tech", ""))
    skills_lang = escape(resume_data.get("skills_languages", ""))
    skills_tools = escape(resume_data.get("skills_tools", ""))
    skills_soft = escape(resume_data.get("skills_soft", ""))

    if skills_tech or skills_lang or skills_tools or skills_soft:
        rows = []
        if skills_lang:
            rows.append(f"<div><strong style='color: #0B132B;'>Languages:</strong> {skills_lang}</div>")
        if skills_tech:
            rows.append(f"<div><strong style='color: #0B132B;'>Backend & Systems:</strong> {skills_tech}</div>")
        if skills_tools:
            rows.append(f"<div><strong style='color: #0B132B;'>Cloud, DevOps & Tooling:</strong> {skills_tools}</div>")
        if skills_soft:
            rows.append(f"<div><strong style='color: #0B132B;'>Engineering Practices:</strong> {skills_soft}</div>")
        skills_html = section_header("Core Technical Stack") + f"<div style='font-size: 12.5px; color: #334155; line-height: 1.6;'>{''.join(rows)}</div>"

    # Projects
    proj_html = ""
    proj_entries = resume_data.get("projects", [])
    proj_blocks = []
    for p in proj_entries:
        title = escape(p.get("title", ""))
        tech = escape(p.get("technologies", ""))
        link = sanitize_link_text(p.get("link", ""))
        desc = _format_bullets_html(p.get("description", ""))
        achieve = _format_bullets_html(p.get("achievements", ""))
        if not title:
            continue
        link_tag = f"<a href='{safe_url(link)}' target='_blank' style='font-size: 11.5px; color: #0284C7; font-weight: 600;'>[Repo / Demo]</a>" if link else ""
        tech_badge = f"<span style='font-size: 11.5px; color: #4338CA; font-weight: 600;'>[{tech}]</span>" if tech else ""
        proj_blocks.append(f"""
        <div style='margin-bottom: 12px;'>
            <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                <div>
                    <strong style='font-size: 13.5px; color: #0B132B;'>{title}</strong>
                    &middot; {tech_badge}
                </div>
                <div>{link_tag}</div>
            </div>
            <div style='font-size: 12.5px; color: #334155;'>{desc}{achieve}</div>
        </div>
        """)
    if proj_blocks:
        proj_html = section_header("Technical Projects & Systems Built") + "".join(proj_blocks)

    # Work Experience
    exp_html = ""
    if not resume_data.get("is_fresher", False):
        exp_entries = resume_data.get("experience", [])
        exp_blocks = []
        for e in exp_entries:
            comp = escape(e.get("company", ""))
            role = escape(e.get("role", ""))
            start = escape(e.get("start_date", ""))
            end = "Present" if e.get("current") else escape(e.get("end_date", ""))
            dates = f"{start} – {end}" if start or end else ""
            desc = _format_bullets_html(e.get("description", ""))
            if not comp and not role:
                continue
            exp_blocks.append(f"""
            <div style='margin-bottom: 12px;'>
                <div style='display: flex; justify-content: space-between;'>
                    <strong style='font-size: 13.5px; color: #0B132B;'>{role} @ {comp}</strong>
                    <span style='font-size: 12px; color: #64748B;'>{dates}</span>
                </div>
                <div style='font-size: 12.5px; color: #334155;'>{desc}</div>
            </div>
            """)
        if exp_blocks:
            exp_html = section_header("Engineering Experience") + "".join(exp_blocks)

    # Education
    edu_html = ""
    edu_entries = resume_data.get("education", [])
    edu_blocks = []
    for ed in edu_entries:
        inst = escape(ed.get("institution", ""))
        deg = escape(ed.get("degree", ""))
        field = escape(ed.get("field", ""))
        s_yr = escape(ed.get("start_year", ""))
        e_yr = escape(ed.get("end_year", ""))
        cgpa = escape(ed.get("cgpa", ""))
        dates = f"{s_yr} – {e_yr}" if s_yr and e_yr else (e_yr or s_yr)
        deg_field = f"{deg}, {field}" if deg and field else (deg or field)
        if not inst and not deg:
            continue
        gpa_str = f" &middot; GPA: {cgpa}" if cgpa else ""
        edu_blocks.append(f"""
        <div style='display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 4px;'>
            <span><strong>{deg_field}</strong> &middot; {inst}{gpa_str}</span>
            <span style='color: #64748B;'>{dates}</span>
        </div>
        """)
    if edu_blocks:
        edu_html = section_header("Education & Credentials") + "".join(edu_blocks)

    return f"""
    <div style='background: #FFFFFF; color: #0B132B; border-radius: 8px; padding: 36px 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace, sans-serif; line-height: 1.5; border: 1px solid #CBD5E1;'>
        <div style='border-bottom: 2px solid #E2E8F0; padding-bottom: 12px;'>
            <div style='font-size: 26px; font-weight: 800; color: #0B132B;'>{name}</div>
            <div style='font-size: 14px; font-weight: 700; color: #0284C7; margin-top: 2px;'>{headline}</div>
            <div style='font-size: 12px; color: #64748B; margin-top: 5px;'>{contact_html}</div>
        </div>

        {f"{section_header('Technical Profile')}<div style='font-size: 12.8px; color: #334155;'>{summary}</div>" if summary else ""}
        {skills_html}
        {proj_html}
        {exp_html}
        {edu_html}
    </div>
    """


# ==============================================================================
# DISPATCHER
# ==============================================================================
def get_resume_preview_html(resume_data: Dict[str, Any], template_name: str = "Modern Professional") -> str:
    """Returns safe, properly formatted HTML string for live preview inside Streamlit."""
    norm = template_name.strip().lower()
    if "minimal" in norm or "ats" in norm:
        raw_html = render_minimal_ats_html(resume_data)
    elif "technical" in norm or "developer" in norm:
        raw_html = render_technical_developer_html(resume_data)
    else:
        raw_html = render_modern_professional_html(resume_data)
    return _clean_html_for_markdown(raw_html)

