"""
AI Resume Screening and Job Matching System - ReportLab Multi-Template PDF Generator.
Supports:
1. Modern Professional (Executive navy & electric blue accents, structured visual hierarchy)
2. Minimal ATS-Friendly (Clean single-column monochrome, standard ATS headers, max parser extraction)
3. Technical / Software Developer (Developer-focused, tech stack highlights, prominent projects & GitHub)

Includes:
- Robust multi-page flow and pagination via NumberedCanvas
- Text-selectable vector output
- PyMuPDF parser compatibility
- Bullet point formatting and metric preservation
"""

import io
import re
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from src.utils import sanitize_filename


def safe_xml(text: Any) -> str:
    """Escapes special XML characters so ReportLab Paragraphs render safely."""
    if not text:
        return ""
    s = str(text)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s.strip()


def safe_link(url: str, label: Optional[str] = None, link_color: str = "#2563EB") -> str:
    """Renders a safe HTML anchor tag for ReportLab Paragraphs."""
    if not url:
        return ""
    clean_url = url.strip()
    if not clean_url:
        return ""
    display_label = label if label else clean_url
    if not (clean_url.startswith("http://") or clean_url.startswith("https://") or clean_url.startswith("mailto:")):
        href = f"https://{clean_url}"
    else:
        href = clean_url
    return f'<font color="{link_color}"><u><a href="{safe_xml(href)}">{safe_xml(display_label)}</a></u></font>'


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to calculate total page count and render professional footers.
    Only displays page numbers if total pages > 1 to keep 1-page resumes clean.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.candidate_name = getattr(self, "candidate_name", "Resume")

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        if page_count > 1:
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            # Running footer: Candidate name on left, Page X of Y on right
            c_name = getattr(self, "candidate_name", "Resume")
            self.drawString(36, 22, f"{c_name} — Curriculum Vitae")
            self.drawRightString(612 - 36, 22, f"Page {self._pageNumber} of {page_count}")
            # Thin subtle rule above footer
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 32, 612 - 36, 32)
            self.restoreState()


def _split_into_bullets(text: str) -> List[str]:
    """Splits description into clean bullet points."""
    if not text:
        return []
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Strip existing bullet markers
        clean = re.sub(r"^[\-\*\•\d+\.]\s*", "", line).strip()
        if clean:
            lines.append(clean)
    return lines


# ==============================================================================
# TEMPLATE 1: MODERN PROFESSIONAL
# ==============================================================================
def _build_modern_professional(doc, resume_data: Dict[str, Any]) -> List[Any]:
    story = []
    styles = getSampleStyleSheet()

    # Colors
    c_primary = colors.HexColor("#1E3A8A")     # Deep Navy
    c_accent = colors.HexColor("#2563EB")      # Electric Blue
    c_dark = colors.HexColor("#0F172A")        # Slate 900
    c_muted = colors.HexColor("#475569")       # Slate 600

    # Custom styles
    style_name = ParagraphStyle(
        "ModName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=25,
        textColor=c_primary
    )
    style_headline = ParagraphStyle(
        "ModHeadline",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=c_accent
    )
    style_contact = ParagraphStyle(
        "ModContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=13,
        textColor=c_muted
    )
    style_section_heading = ParagraphStyle(
        "ModSectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=c_primary,
        spaceAfter=3
    )
    style_item_title = ParagraphStyle(
        "ModItemTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=c_dark
    )
    style_item_sub = ParagraphStyle(
        "ModItemSub",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=c_muted
    )
    style_date = ParagraphStyle(
        "ModDate",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        alignment=TA_RIGHT,
        textColor=c_muted
    )
    style_body = ParagraphStyle(
        "ModBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_dark
    )
    style_bullet = ParagraphStyle(
        "ModBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12.5,
        textColor=c_dark,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2
    )

    def add_section_header(title: str):
        story.append(Spacer(1, 8))
        story.append(Paragraph(safe_xml(title.upper()), style_section_heading))
        story.append(HRFlowable(width="100%", thickness=1.2, color=c_primary, spaceBefore=2, spaceAfter=6))

    # --- Header ---
    full_name = resume_data.get("full_name") or "Candidate Name"
    headline = resume_data.get("headline") or ""
    story.append(Paragraph(safe_xml(full_name), style_name))
    if headline:
        story.append(Spacer(1, 2))
        story.append(Paragraph(safe_xml(headline), style_headline))

    # Contact row
    contact_parts = []
    if resume_data.get("email"):
        contact_parts.append(safe_link(f"mailto:{resume_data['email']}", resume_data['email'], link_color="#1E3A8A"))
    if resume_data.get("phone"):
        contact_parts.append(safe_xml(resume_data['phone']))
    if resume_data.get("location"):
        contact_parts.append(safe_xml(resume_data['location']))
    if resume_data.get("linkedin"):
        contact_parts.append(safe_link(resume_data['linkedin'], "LinkedIn", link_color="#2563EB"))
    if resume_data.get("github"):
        contact_parts.append(safe_link(resume_data['github'], "GitHub", link_color="#2563EB"))
    if resume_data.get("portfolio"):
        contact_parts.append(safe_link(resume_data['portfolio'], "Portfolio", link_color="#2563EB"))

    if contact_parts:
        story.append(Spacer(1, 4))
        contact_html = " &bull; ".join(contact_parts)
        story.append(Paragraph(contact_html, style_contact))

    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceBefore=4, spaceAfter=6))

    # --- Summary ---
    if resume_data.get("summary"):
        add_section_header("Professional Summary")
        story.append(Paragraph(safe_xml(resume_data["summary"]), style_body))

    # --- Skills ---
    skills_tech = resume_data.get("skills_tech", "").strip()
    skills_lang = resume_data.get("skills_languages", "").strip()
    skills_tools = resume_data.get("skills_tools", "").strip()
    skills_soft = resume_data.get("skills_soft", "").strip()

    if skills_tech or skills_lang or skills_tools or skills_soft:
        add_section_header("Skills & Competencies")
        skill_rows = []
        if skills_lang:
            skill_rows.append(Paragraph(f"<b>Languages:</b> {safe_xml(skills_lang)}", style_body))
        if skills_tech:
            skill_rows.append(Paragraph(f"<b>Technical Skills:</b> {safe_xml(skills_tech)}", style_body))
        if skills_tools:
            skill_rows.append(Paragraph(f"<b>Frameworks & Tools:</b> {safe_xml(skills_tools)}", style_body))
        if skills_soft:
            skill_rows.append(Paragraph(f"<b>Soft Skills:</b> {safe_xml(skills_soft)}", style_body))

        for sr in skill_rows:
            story.append(sr)
            story.append(Spacer(1, 2))

    # --- Work Experience ---
    is_fresher = resume_data.get("is_fresher", False)
    experience_list = resume_data.get("experience", [])
    if not is_fresher and experience_list:
        add_section_header("Work Experience")
        for exp in experience_list:
            comp = exp.get("company", "").strip()
            role = exp.get("role", "").strip()
            start = exp.get("start_date", "").strip()
            end = "Present" if exp.get("current") else exp.get("end_date", "").strip()
            date_str = f"{start} – {end}" if start or end else ""
            desc = exp.get("description", "").strip()

            if not comp and not role:
                continue

            entry_story = []
            header_table_data = [
                [Paragraph(safe_xml(role), style_item_title), Paragraph(safe_xml(date_str), style_date)]
            ]
            t = Table(header_table_data, colWidths=[380, 160])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Paragraph(safe_xml(comp), style_item_sub))
            entry_story.append(Spacer(1, 3))

            bullets = _split_into_bullets(desc)
            if bullets:
                for b in bullets:
                    entry_story.append(Paragraph(f"&bull; {safe_xml(b)}", style_bullet))
            elif desc:
                entry_story.append(Paragraph(safe_xml(desc), style_body))

            entry_story.append(Spacer(1, 6))
            story.append(KeepTogether(entry_story))

    # --- Projects ---
    projects_list = resume_data.get("projects", [])
    if projects_list:
        add_section_header("Key Projects")
        for proj in projects_list:
            title = proj.get("title", "").strip()
            tech = proj.get("technologies", "").strip()
            link = proj.get("link", "").strip()
            desc = proj.get("description", "").strip()
            achieve = proj.get("achievements", "").strip()

            if not title:
                continue

            entry_story = []
            link_html = safe_link(link, "Link / Repository") if link else ""
            tech_str = f" | <i>{safe_xml(tech)}</i>" if tech else ""
            title_html = f"<b>{safe_xml(title)}</b>{tech_str}"

            header_table_data = [
                [Paragraph(title_html, style_item_title), Paragraph(link_html, style_date)]
            ]
            t = Table(header_table_data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Spacer(1, 2))

            combined_bullets = _split_into_bullets(desc) + _split_into_bullets(achieve)
            if combined_bullets:
                for b in combined_bullets:
                    entry_story.append(Paragraph(f"&bull; {safe_xml(b)}", style_bullet))
            elif desc:
                entry_story.append(Paragraph(safe_xml(desc), style_body))

            entry_story.append(Spacer(1, 5))
            story.append(KeepTogether(entry_story))

    # --- Education ---
    edu_list = resume_data.get("education", [])
    if edu_list:
        add_section_header("Education")
        for edu in edu_list:
            inst = edu.get("institution", "").strip()
            deg = edu.get("degree", "").strip()
            field = edu.get("field", "").strip()
            s_yr = edu.get("start_year", "").strip()
            e_yr = edu.get("end_year", "").strip()
            cgpa = edu.get("cgpa", "").strip()

            if not inst and not deg:
                continue

            entry_story = []
            deg_field = f"{deg} in {field}" if deg and field else (deg or field)
            date_str = f"{s_yr} – {e_yr}" if s_yr and e_yr else (e_yr or s_yr)

            header_table_data = [
                [Paragraph(safe_xml(deg_field), style_item_title), Paragraph(safe_xml(date_str), style_date)]
            ]
            t = Table(header_table_data, colWidths=[420, 120])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            sub_info = safe_xml(inst)
            if cgpa:
                sub_info += f" &bull; <b>CGPA / Score:</b> {safe_xml(cgpa)}"
            entry_story.append(Paragraph(sub_info, style_item_sub))
            entry_story.append(Spacer(1, 4))
            story.append(KeepTogether(entry_story))

    # --- Certifications & Achievements ---
    certs = resume_data.get("certifications", [])
    if certs:
        add_section_header("Certifications & Achievements")
        for c in certs:
            name = c.get("name", "").strip()
            issuer = c.get("issuer", "").strip()
            year = c.get("year", "").strip()
            details = c.get("details", "").strip()

            if not name:
                continue

            line = f"<b>{safe_xml(name)}</b>"
            if issuer:
                line += f" — {safe_xml(issuer)}"
            if year:
                line += f" ({safe_xml(year)})"
            if details:
                line += f": {safe_xml(details)}"
            story.append(Paragraph(f"&bull; {line}", style_bullet))

    # --- Additional Information ---
    add_info = resume_data.get("additional_sections", {})
    if add_info:
        for title, content in add_info.items():
            if content and content.strip():
                add_section_header(title)
                for b in _split_into_bullets(content):
                    story.append(Paragraph(f"&bull; {safe_xml(b)}", style_bullet))

    return story


# ==============================================================================
# TEMPLATE 2: MINIMAL ATS-FRIENDLY
# ==============================================================================
def _build_minimal_ats(doc, resume_data: Dict[str, Any]) -> List[Any]:
    story = []
    styles = getSampleStyleSheet()

    c_black = colors.HexColor("#000000")
    c_dark = colors.HexColor("#1F2937")
    c_line = colors.HexColor("#4B5563")

    style_name = ParagraphStyle(
        "ATSName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=c_black
    )
    style_headline = ParagraphStyle(
        "ATSHeadline",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=c_dark
    )
    style_contact = ParagraphStyle(
        "ATSContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=c_dark
    )
    style_section_heading = ParagraphStyle(
        "ATSSectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=c_black,
        spaceAfter=2
    )
    style_item_title = ParagraphStyle(
        "ATSItemTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12.5,
        textColor=c_black
    )
    style_item_sub = ParagraphStyle(
        "ATSItemSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=c_dark
    )
    style_date = ParagraphStyle(
        "ATSDate",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        alignment=TA_RIGHT,
        textColor=c_black
    )
    style_body = ParagraphStyle(
        "ATSBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12.5,
        textColor=c_dark,
        alignment=TA_JUSTIFY
    )
    style_bullet = ParagraphStyle(
        "ATSBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12.5,
        textColor=c_black,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2
    )

    def add_section_header(title: str):
        story.append(Spacer(1, 8))
        story.append(Paragraph(safe_xml(title.upper()), style_section_heading))
        story.append(HRFlowable(width="100%", thickness=0.8, color=c_line, spaceBefore=2, spaceAfter=5))

    # --- Header ---
    full_name = resume_data.get("full_name") or "Candidate Name"
    headline = resume_data.get("headline") or ""
    story.append(Paragraph(safe_xml(full_name.upper()), style_name))
    if headline:
        story.append(Spacer(1, 2))
        story.append(Paragraph(safe_xml(headline), style_headline))

    contact_parts = []
    if resume_data.get("email"):
        contact_parts.append(safe_xml(resume_data['email']))
    if resume_data.get("phone"):
        contact_parts.append(safe_xml(resume_data['phone']))
    if resume_data.get("location"):
        contact_parts.append(safe_xml(resume_data['location']))
    if resume_data.get("linkedin"):
        contact_parts.append(safe_xml(resume_data['linkedin']))
    if resume_data.get("github"):
        contact_parts.append(safe_xml(resume_data['github']))
    if resume_data.get("portfolio"):
        contact_parts.append(safe_xml(resume_data['portfolio']))

    if contact_parts:
        story.append(Spacer(1, 3))
        story.append(Paragraph(" | ".join(contact_parts), style_contact))

    story.append(Spacer(1, 3))

    # --- Summary ---
    if resume_data.get("summary"):
        add_section_header("Professional Summary")
        story.append(Paragraph(safe_xml(resume_data["summary"]), style_body))

    # --- Skills ---
    skills_tech = resume_data.get("skills_tech", "").strip()
    skills_lang = resume_data.get("skills_languages", "").strip()
    skills_tools = resume_data.get("skills_tools", "").strip()
    skills_soft = resume_data.get("skills_soft", "").strip()

    if skills_tech or skills_lang or skills_tools or skills_soft:
        add_section_header("Technical Skills")
        if skills_lang:
            story.append(Paragraph(f"<b>Programming Languages:</b> {safe_xml(skills_lang)}", style_body))
        if skills_tech:
            story.append(Paragraph(f"<b>Technologies & Methodologies:</b> {safe_xml(skills_tech)}", style_body))
        if skills_tools:
            story.append(Paragraph(f"<b>Frameworks & Tools:</b> {safe_xml(skills_tools)}", style_body))
        if skills_soft:
            story.append(Paragraph(f"<b>Core Competencies:</b> {safe_xml(skills_soft)}", style_body))

    # --- Work Experience ---
    is_fresher = resume_data.get("is_fresher", False)
    experience_list = resume_data.get("experience", [])
    if not is_fresher and experience_list:
        add_section_header("Professional Experience")
        for exp in experience_list:
            comp = exp.get("company", "").strip()
            role = exp.get("role", "").strip()
            start = exp.get("start_date", "").strip()
            end = "Present" if exp.get("current") else exp.get("end_date", "").strip()
            date_str = f"{start} – {end}" if start or end else ""
            desc = exp.get("description", "").strip()

            if not comp and not role:
                continue

            entry_story = []
            header_table_data = [
                [Paragraph(f"<b>{safe_xml(role)}</b>, {safe_xml(comp)}", style_item_title), Paragraph(safe_xml(date_str), style_date)]
            ]
            t = Table(header_table_data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Spacer(1, 2))

            bullets = _split_into_bullets(desc)
            if bullets:
                for b in bullets:
                    entry_story.append(Paragraph(f"&bull; {safe_xml(b)}", style_bullet))
            elif desc:
                entry_story.append(Paragraph(safe_xml(desc), style_body))

            entry_story.append(Spacer(1, 4))
            story.append(KeepTogether(entry_story))

    # --- Projects ---
    projects_list = resume_data.get("projects", [])
    if projects_list:
        add_section_header("Projects")
        for proj in projects_list:
            title = proj.get("title", "").strip()
            tech = proj.get("technologies", "").strip()
            link = proj.get("link", "").strip()
            desc = proj.get("description", "").strip()
            achieve = proj.get("achievements", "").strip()

            if not title:
                continue

            entry_story = []
            title_text = f"<b>{safe_xml(title)}</b>"
            if tech:
                title_text += f" | <i>{safe_xml(tech)}</i>"

            link_text = safe_xml(link) if link else ""
            header_table_data = [
                [Paragraph(title_text, style_item_title), Paragraph(link_text, style_date)]
            ]
            t = Table(header_table_data, colWidths=[410, 130])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Spacer(1, 2))

            combined_bullets = _split_into_bullets(desc) + _split_into_bullets(achieve)
            if combined_bullets:
                for b in combined_bullets:
                    entry_story.append(Paragraph(f"&bull; {safe_xml(b)}", style_bullet))
            elif desc:
                entry_story.append(Paragraph(safe_xml(desc), style_body))

            entry_story.append(Spacer(1, 4))
            story.append(KeepTogether(entry_story))

    # --- Education ---
    edu_list = resume_data.get("education", [])
    if edu_list:
        add_section_header("Education")
        for edu in edu_list:
            inst = edu.get("institution", "").strip()
            deg = edu.get("degree", "").strip()
            field = edu.get("field", "").strip()
            s_yr = edu.get("start_year", "").strip()
            e_yr = edu.get("end_year", "").strip()
            cgpa = edu.get("cgpa", "").strip()

            if not inst and not deg:
                continue

            entry_story = []
            deg_field = f"<b>{safe_xml(deg)}</b>"
            if field:
                deg_field += f" in {safe_xml(field)}"
            deg_field += f", {safe_xml(inst)}"
            if cgpa:
                deg_field += f" (GPA: {safe_xml(cgpa)})"

            date_str = f"{s_yr} – {e_yr}" if s_yr and e_yr else (e_yr or s_yr)

            header_table_data = [
                [Paragraph(deg_field, style_item_title), Paragraph(safe_xml(date_str), style_date)]
            ]
            t = Table(header_table_data, colWidths=[420, 120])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Spacer(1, 3))
            story.append(KeepTogether(entry_story))

    # --- Certifications ---
    certs = resume_data.get("certifications", [])
    if certs:
        add_section_header("Certifications & Awards")
        for c in certs:
            name = c.get("name", "").strip()
            issuer = c.get("issuer", "").strip()
            year = c.get("year", "").strip()
            details = c.get("details", "").strip()

            if not name:
                continue

            line = f"<b>{safe_xml(name)}</b>"
            if issuer:
                line += f" – {safe_xml(issuer)}"
            if year:
                line += f" ({safe_xml(year)})"
            if details:
                line += f": {safe_xml(details)}"
            story.append(Paragraph(f"&bull; {line}", style_bullet))

    return story


# ==============================================================================
# TEMPLATE 3: TECHNICAL / SOFTWARE DEVELOPER
# ==============================================================================
def _build_technical_developer(doc, resume_data: Dict[str, Any]) -> List[Any]:
    story = []
    styles = getSampleStyleSheet()

    c_dark = colors.HexColor("#0B132B")        # Midnight Blue/Dark Slate
    c_cyan = colors.HexColor("#0284C7")        # Electric Cyan/Sky
    c_indigo = colors.HexColor("#4338CA")      # Rich Indigo
    c_muted = colors.HexColor("#475569")       # Slate Muted

    style_name = ParagraphStyle(
        "TechName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=c_dark
    )
    style_headline = ParagraphStyle(
        "TechHeadline",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=c_cyan
    )
    style_contact = ParagraphStyle(
        "TechContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=13,
        textColor=c_muted
    )
    style_section_heading = ParagraphStyle(
        "TechSectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=c_indigo,
        spaceAfter=2
    )
    style_item_title = ParagraphStyle(
        "TechItemTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=c_dark
    )
    style_item_sub = ParagraphStyle(
        "TechItemSub",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=c_cyan
    )
    style_date = ParagraphStyle(
        "TechDate",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        alignment=TA_RIGHT,
        textColor=c_muted
    )
    style_body = ParagraphStyle(
        "TechBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_dark
    )
    style_bullet = ParagraphStyle(
        "TechBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12.5,
        textColor=c_dark,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2
    )

    def add_section_header(title: str):
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"// {safe_xml(title.upper())}", style_section_heading))
        story.append(HRFlowable(width="100%", thickness=1.0, color=c_indigo, spaceBefore=2, spaceAfter=6))

    # --- Header ---
    full_name = resume_data.get("full_name") or "Candidate Name"
    headline = resume_data.get("headline") or "Software Engineer"
    story.append(Paragraph(safe_xml(full_name), style_name))
    story.append(Spacer(1, 2))
    story.append(Paragraph(safe_xml(headline), style_headline))

    contact_parts = []
    if resume_data.get("email"):
        contact_parts.append(safe_link(f"mailto:{resume_data['email']}", resume_data['email'], link_color="#0284C7"))
    if resume_data.get("phone"):
        contact_parts.append(safe_xml(resume_data['phone']))
    if resume_data.get("location"):
        contact_parts.append(safe_xml(resume_data['location']))
    if resume_data.get("github"):
        contact_parts.append(safe_link(resume_data['github'], "github.com", link_color="#0284C7"))
    if resume_data.get("portfolio"):
        contact_parts.append(safe_link(resume_data['portfolio'], "portfolio", link_color="#0284C7"))
    if resume_data.get("linkedin"):
        contact_parts.append(safe_link(resume_data['linkedin'], "linkedin", link_color="#0284C7"))

    if contact_parts:
        story.append(Spacer(1, 4))
        story.append(Paragraph(" &middot; ".join(contact_parts), style_contact))

    story.append(Spacer(1, 4))

    # --- Summary ---
    if resume_data.get("summary"):
        add_section_header("Technical Profile")
        story.append(Paragraph(safe_xml(resume_data["summary"]), style_body))

    # --- Technical Skills (Placed high for developers!) ---
    skills_tech = resume_data.get("skills_tech", "").strip()
    skills_lang = resume_data.get("skills_languages", "").strip()
    skills_tools = resume_data.get("skills_tools", "").strip()
    skills_soft = resume_data.get("skills_soft", "").strip()

    if skills_tech or skills_lang or skills_tools or skills_soft:
        add_section_header("Core Technical Stack")
        if skills_lang:
            story.append(Paragraph(f"<b>Languages:</b> {safe_xml(skills_lang)}", style_body))
        if skills_tech:
            story.append(Paragraph(f"<b>Backend & Systems:</b> {safe_xml(skills_tech)}", style_body))
        if skills_tools:
            story.append(Paragraph(f"<b>Cloud, DevOps & Tooling:</b> {safe_xml(skills_tools)}", style_body))
        if skills_soft:
            story.append(Paragraph(f"<b>Engineering Practices:</b> {safe_xml(skills_soft)}", style_body))

    # --- Projects (Featured Prominently) ---
    projects_list = resume_data.get("projects", [])
    if projects_list:
        add_section_header("Technical Projects & Systems Built")
        for proj in projects_list:
            title = proj.get("title", "").strip()
            tech = proj.get("technologies", "").strip()
            link = proj.get("link", "").strip()
            desc = proj.get("description", "").strip()
            achieve = proj.get("achievements", "").strip()

            if not title:
                continue

            entry_story = []
            link_html = safe_link(link, "[Repo / Demo]", link_color="#0284C7") if link else ""
            title_html = f"<b>{safe_xml(title)}</b>"
            if tech:
                title_html += f" &middot; <i><font color='#4338CA'>[{safe_xml(tech)}]</font></i>"

            header_table_data = [
                [Paragraph(title_html, style_item_title), Paragraph(link_html, style_date)]
            ]
            t = Table(header_table_data, colWidths=[420, 120])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Spacer(1, 2))

            combined_bullets = _split_into_bullets(desc) + _split_into_bullets(achieve)
            if combined_bullets:
                for b in combined_bullets:
                    entry_story.append(Paragraph(f"&bull; {safe_xml(b)}", style_bullet))
            elif desc:
                entry_story.append(Paragraph(safe_xml(desc), style_body))

            entry_story.append(Spacer(1, 5))
            story.append(KeepTogether(entry_story))

    # --- Work Experience ---
    is_fresher = resume_data.get("is_fresher", False)
    experience_list = resume_data.get("experience", [])
    if not is_fresher and experience_list:
        add_section_header("Engineering Experience")
        for exp in experience_list:
            comp = exp.get("company", "").strip()
            role = exp.get("role", "").strip()
            start = exp.get("start_date", "").strip()
            end = "Present" if exp.get("current") else exp.get("end_date", "").strip()
            date_str = f"{start} – {end}" if start or end else ""
            desc = exp.get("description", "").strip()

            if not comp and not role:
                continue

            entry_story = []
            header_table_data = [
                [Paragraph(f"<b>{safe_xml(role)}</b> @ {safe_xml(comp)}", style_item_title), Paragraph(safe_xml(date_str), style_date)]
            ]
            t = Table(header_table_data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Spacer(1, 2))

            bullets = _split_into_bullets(desc)
            if bullets:
                for b in bullets:
                    entry_story.append(Paragraph(f"&bull; {safe_xml(b)}", style_bullet))
            elif desc:
                entry_story.append(Paragraph(safe_xml(desc), style_body))

            entry_story.append(Spacer(1, 5))
            story.append(KeepTogether(entry_story))

    # --- Education ---
    edu_list = resume_data.get("education", [])
    if edu_list:
        add_section_header("Education & Credentials")
        for edu in edu_list:
            inst = edu.get("institution", "").strip()
            deg = edu.get("degree", "").strip()
            field = edu.get("field", "").strip()
            s_yr = edu.get("start_year", "").strip()
            e_yr = edu.get("end_year", "").strip()
            cgpa = edu.get("cgpa", "").strip()

            if not inst and not deg:
                continue

            entry_story = []
            deg_field = f"<b>{safe_xml(deg)}</b>"
            if field:
                deg_field += f", {safe_xml(field)}"
            deg_field += f" &middot; {safe_xml(inst)}"
            if cgpa:
                deg_field += f" (GPA: {safe_xml(cgpa)})"

            date_str = f"{s_yr} – {e_yr}" if s_yr and e_yr else (e_yr or s_yr)

            header_table_data = [
                [Paragraph(deg_field, style_item_title), Paragraph(safe_xml(date_str), style_date)]
            ]
            t = Table(header_table_data, colWidths=[420, 120])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0)
            ]))
            entry_story.append(t)
            entry_story.append(Spacer(1, 3))
            story.append(KeepTogether(entry_story))

    # --- Certifications ---
    certs = resume_data.get("certifications", [])
    if certs:
        add_section_header("Certifications & Hackathons")
        for c in certs:
            name = c.get("name", "").strip()
            issuer = c.get("issuer", "").strip()
            year = c.get("year", "").strip()
            details = c.get("details", "").strip()

            if not name:
                continue

            line = f"<b>{safe_xml(name)}</b>"
            if issuer:
                line += f" | {safe_xml(issuer)}"
            if year:
                line += f" ({safe_xml(year)})"
            if details:
                line += f": {safe_xml(details)}"
            story.append(Paragraph(f"&bull; {line}", style_bullet))

    return story


# ==============================================================================
# MAIN PDF GENERATION DISPATCHER
# ==============================================================================
def generate_resume_pdf(resume_data: Dict[str, Any], template_name: str = "Modern Professional") -> bytes:
    """
    Generates a professional multi-page PDF resume using ReportLab.
    Returns bytes of the compiled PDF.
    """
    buffer = io.BytesIO()
    margin = 36  # 0.5 inch margins

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    norm_template = template_name.strip().lower()

    if "minimal" in norm_template or "ats" in norm_template:
        story = _build_minimal_ats(doc, resume_data)
    elif "technical" in norm_template or "developer" in norm_template:
        story = _build_technical_developer(doc, resume_data)
    else:
        # Default: Modern Professional
        story = _build_modern_professional(doc, resume_data)

    # Set candidate name on canvas for running header/footer
    c_name = resume_data.get("full_name") or "Candidate"

    def canvas_factory(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c.candidate_name = c_name
        return c

    doc.build(story, canvasmaker=canvas_factory)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def get_download_filename(candidate_name: Optional[str]) -> str:
    """Returns a clean, standardized filename for the downloaded PDF."""
    if not candidate_name or not candidate_name.strip():
        return "TalentIQ_Candidate_Resume.pdf"
    clean_name = candidate_name.replace("/", " ").replace("\\", " ")
    clean = sanitize_filename(clean_name.strip()).replace(" ", "_")
    clean = re.sub(r"_+", "_", clean).strip("_")
    return f"{clean}_Resume.pdf"
