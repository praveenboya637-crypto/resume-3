"""
AI Resume Screening and Job Matching System - Resume Quality & ATS Completeness Engine.
Provides comprehensive scoring, missing section diagnostics, actionable suggestions,
metric detection, action-verb analysis, and target-role ATS keyword guidance.
"""

import re
from typing import Dict, List, Any, Optional
from src.constants import SKILL_TAXONOMY, SAMPLE_JOB_DESCRIPTIONS
from src.skills_extractor import extract_skills_from_text


# High-impact action verbs organized by functional focus
ACTION_VERBS = {
    "Engineering & Development": [
        "Architected", "Engineered", "Developed", "Built", "Implemented", "Designed",
        "Programmed", "Deployed", "Refactored", "Containerized", "Automated", "Constructed"
    ],
    "Optimization & Performance": [
        "Optimized", "Accelerated", "Streamlined", "Reduced", "Boosted", "Enhanced",
        "Maximized", "Minimized", "Scaled", "Revamped", "Benchmarked", "Consolidated"
    ],
    "Leadership & Delivery": [
        "Spearheaded", "Led", "Directed", "Orchestrated", "Championed", "Mentored",
        "Coordinated", "Guided", "Executed", "Supervised", "Facilitated", "Managed"
    ],
    "Analysis & Research": [
        "Analyzed", "Evaluated", "Investigated", "Diagnosed", "Identified", "Synthesized",
        "Formulated", "Validated", "Audited", "Modeled", "Tested", "Researched"
    ]
}

FLAT_ACTION_VERBS = {v.lower() for sublist in ACTION_VERBS.values() for v in sublist}

# Target Role Skill Recommendations based on industry standards
ROLE_RECOMMENDATIONS = {
    "AI / Machine Learning Engineer": [
        "Python", "PyTorch", "TensorFlow", "Scikit-Learn", "Docker", "FastAPI",
        "Transformers", "LLM", "Deep Learning", "NLP", "Git", "MLops", "CI/CD"
    ],
    "Full Stack Developer": [
        "JavaScript", "TypeScript", "React", "Node.js", "Python", "FastAPI",
        "PostgreSQL", "Docker", "REST API", "Git", "Tailwind CSS", "MongoDB"
    ],
    "Data Scientist / Analyst": [
        "Python", "SQL", "Pandas", "NumPy", "Scikit-Learn", "Tableau",
        "Power BI", "Data Analysis", "Statistics", "Data Visualization", "Matplotlib"
    ],
    "DevOps & Cloud Engineer": [
        "Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Terraform",
        "Git", "Bash", "Prometheus", "Ansible", "Python", "Microservices"
    ],
    "Backend Software Engineer": [
        "Python", "Java", "Go", "FastAPI", "Spring Boot", "PostgreSQL",
        "Redis", "Docker", "REST API", "Microservices", "System Design", "Git"
    ],
    "Frontend Developer": [
        "JavaScript", "TypeScript", "React", "Next.js", "HTML5", "CSS3",
        "Tailwind CSS", "Redux", "REST API", "Git", "Webpack", "UI/UX"
    ]
}


def _detect_metrics(text: str) -> List[str]:
    """Detects numbers, percentages, dollar values, and metrics in bullet points."""
    if not text:
        return []
    metric_patterns = [
        r"\b\d+%",                                    # 45%
        r"\b\d+\s*percent\b",                         # 20 percent
        r"\$\s*\d+[\d,]*\.?\d*\s*(?:k|m|b|million|billion)?\b", # $50k, $1.2M
        r"\b\d+[\d,]*\s*(?:users|clients|requests|qps|rpm|records|queries|rows|nodes)\b", # 10000 users
        r"\b(?:reduced|increased|improved|boosted|accelerated|saved|cut)\s+(?:by\s+)?\d+[%xX]?", # reduced by 40%
        r"\b\d+x\b",                                  # 10x
        r"\b\d+\+?\s*(?:ms|sec|seconds|minutes|hours|days)\b" # 200ms
    ]
    matches = []
    for pat in metric_patterns:
        found = re.findall(pat, text, re.IGNORECASE)
        for f in found:
            if isinstance(f, str) and f.strip():
                matches.append(f.strip())
    return list(dict.fromkeys(matches))


def _has_action_verb(text: str) -> bool:
    """Checks if a bullet sentence starts with an active verb."""
    if not text:
        return False
    words = re.findall(r"[A-Za-z]+", text.strip())
    if not words:
        return False
    first_word = words[0].lower()
    return first_word in FLAT_ACTION_VERBS


def evaluate_resume_quality(resume_data: Dict[str, Any], target_role: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates a candidate's resume data for completeness, ATS compatibility,
    metric evidence, and formatting best practices.
    Returns:
        - score: float (0 - 100)
        - rating: str (Outstanding / Strong / Good / Needs Improvement)
        - strengths: list of verified facts supplied by candidate
        - suggestions: list of constructive improvement recommendations
        - critical_missing: list of essential missing items
        - metrics_found: list of quantifiable metrics detected
        - action_verbs_detected: list of action verbs found
        - role_keywords_advice: dict with recommended vs included skills
    """
    score = 0.0
    strengths = []
    suggestions = []
    critical_missing = []
    metrics_detected = []
    action_verbs_found = []

    # 1. Contact Information Evaluation (25 pts max)
    name = (resume_data.get("full_name") or "").strip()
    headline = (resume_data.get("headline") or "").strip()
    email = (resume_data.get("email") or "").strip()
    phone = (resume_data.get("phone") or "").strip()
    location = (resume_data.get("location") or "").strip()
    linkedin = (resume_data.get("linkedin") or "").strip()
    github = (resume_data.get("github") or "").strip()
    portfolio = (resume_data.get("portfolio") or "").strip()

    if name:
        score += 5.0
        strengths.append(f"Full name '{name}' provided clearly.")
    else:
        critical_missing.append("Candidate Full Name is required.")

    if headline:
        score += 4.0
        strengths.append(f"Target headline specified: '{headline}'.")
    else:
        suggestions.append("Add a professional headline (e.g. 'Senior Full Stack Developer' or 'AI/ML Specialist') to establish immediate relevance.")

    if email and re.search(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        score += 5.0
    elif email:
        score += 2.0
        suggestions.append("Check email format; ensure a valid professional address (e.g. name@domain.com).")
    else:
        critical_missing.append("Email address is missing.")

    if phone:
        score += 4.0
    else:
        suggestions.append("Add a phone number so hiring teams and recruiter phone screens can reach you.")

    if location:
        score += 3.0
    else:
        suggestions.append("Include city and state/country (e.g. 'Austin, TX' or 'Remote') for local or timezone-matched hiring.")

    profiles_count = sum(1 for p in [linkedin, github, portfolio] if p)
    if profiles_count >= 2:
        score += 4.0
        strengths.append(f"Strong digital footprint with {profiles_count} profile/portfolio links.")
    elif profiles_count == 1:
        score += 2.0
        suggestions.append("Consider adding a GitHub profile or personal portfolio URL to substantiate your work.")
    else:
        suggestions.append("Adding professional profile links (LinkedIn, GitHub, or Portfolio) significantly increases recruiter response rates.")

    # 2. Professional Summary Evaluation (15 pts max)
    summary = (resume_data.get("summary") or "").strip()
    summary_words = len(summary.split()) if summary else 0
    if summary_words >= 35:
        score += 15.0
        strengths.append(f"Comprehensive professional summary ({summary_words} words) highlighting core domain experience.")
    elif summary_words >= 15:
        score += 10.0
        suggestions.append("Expand professional summary slightly (aim for 35–60 words) highlighting years of experience, core tech stack, and primary career impact.")
    elif summary_words > 0:
        score += 5.0
        suggestions.append("Professional summary is too brief. Elaborate on your engineering focus and notable strengths.")
    else:
        suggestions.append("Include a 3-4 sentence professional summary or career objective at the top of your resume.")

    # 3. Skills Evaluation (15 pts max)
    # Collect all skill inputs
    all_skills_text = " ".join([
        resume_data.get("skills_tech", ""),
        resume_data.get("skills_languages", ""),
        resume_data.get("skills_tools", ""),
        resume_data.get("skills_soft", "")
    ])
    extracted_skills_dict = extract_skills_from_text(all_skills_text)
    detected_skills = extracted_skills_dict.get("display_skills") or extracted_skills_dict.get("all_skills") or []
    skill_count = len(detected_skills)

    if skill_count >= 10:
        score += 15.0
        strengths.append(f"Robust skill taxonomy with {skill_count} recognized industry skills across categories.")
    elif skill_count >= 5:
        score += 10.0
        suggestions.append(f"Good skills foundation ({skill_count} skills). Adding a few more specific frameworks, databases, or cloud tools enhances keyword matching.")
    elif skill_count > 0:
        score += 5.0
        suggestions.append(f"Only {skill_count} recognized skills detected. Group skills into Technical Languages, Frameworks, and Tools for better ATS indexing.")
    else:
        critical_missing.append("Technical Skills section is empty. ATS systems rely heavily on skill keywords.")

    # 4. Education Evaluation (15 pts max)
    education_entries = resume_data.get("education", [])
    valid_edu = [e for e in education_entries if (e.get("institution") or "").strip() and (e.get("degree") or "").strip()]
    if valid_edu:
        score += 15.0
        strengths.append(f"Education verified: {len(valid_edu)} degree entry/entries listed.")
        for e in valid_edu:
            if not e.get("end_year"):
                suggestions.append(f"Include completion or expected graduation year for {e.get('degree')} at {e.get('institution')}.")
    else:
        critical_missing.append("At least one Education entry (Institution and Degree) is required.")

    # 5. Work Experience & Projects Evaluation (20 pts max)
    is_fresher = resume_data.get("is_fresher", False)
    experience_entries = resume_data.get("experience", [])
    valid_exp = [e for e in experience_entries if (e.get("company") or "").strip() and (e.get("role") or "").strip()]
    projects_entries = resume_data.get("projects", [])
    valid_proj = [p for p in projects_entries if (p.get("title") or "").strip() and (p.get("description") or "").strip()]

    if is_fresher:
        # For freshers, experience is skipped; evaluate projects more heavily
        strengths.append("Fresher profile configured: evaluated with focus on academic projects, skills, and coursework.")
        if len(valid_proj) >= 2:
            score += 20.0
            strengths.append(f"Strong project portfolio with {len(valid_proj)} detailed technical projects.")
        elif len(valid_proj) == 1:
            score += 12.0
            suggestions.append("Freshers are strongly encouraged to include at least 2 distinct technical projects to demonstrate hands-on execution.")
        else:
            critical_missing.append("No projects listed. For freshers, projects are the primary evidence of practical competence.")
    else:
        # For experienced candidates
        if len(valid_exp) >= 2:
            score += 14.0
            strengths.append(f"{len(valid_exp)} professional work experience roles documented.")
        elif len(valid_exp) == 1:
            score += 10.0
            strengths.append(f"Work experience at {valid_exp[0].get('company')} documented.")
        else:
            suggestions.append("No work experience added. If you are an entry-level candidate or graduate, toggle 'I am a Fresher' to tailor the resume.")

        if valid_proj:
            score += 6.0
            strengths.append(f"{len(valid_proj)} showcased project(s) reinforcing professional experience.")
        else:
            score += 2.0
            suggestions.append("Adding 1-2 featured projects with GitHub links provides tangible proof of engineering capabilities.")

    # 6. Quantifiable Metrics & Action Verbs Analysis (10 pts max)
    # Collect all bullet / description text from experience and projects
    all_body_text = []
    for exp in valid_exp:
        all_body_text.append(exp.get("description", ""))
    for proj in valid_proj:
        all_body_text.append(proj.get("description", ""))
        all_body_text.append(proj.get("achievements", ""))
    full_narrative = "\n".join(all_body_text)

    # Detect metrics
    found_metrics = _detect_metrics(full_narrative)
    metrics_detected.extend(found_metrics)

    # Detect action verbs in bullet points
    lines = [line.strip().lstrip("-•*").strip() for line in full_narrative.split("\n") if line.strip()]
    for line in lines:
        words = re.findall(r"[A-Za-z]+", line)
        if words and words[0].lower() in FLAT_ACTION_VERBS:
            action_verbs_found.append(words[0].capitalize())

    action_verbs_found = list(dict.fromkeys(action_verbs_found))

    if found_metrics:
        score += 5.0
        strengths.append(f"Measurable achievements detected ({len(found_metrics)} metrics, e.g. {', '.join(found_metrics[:3])}).")
    else:
        suggestions.append("Include quantifiable impact in your bullet points (e.g. 'reduced latency by 35%', 'scaled system to 50k users', 'saved 12 hours/week').")

    if len(action_verbs_found) >= 3:
        score += 5.0
        strengths.append(f"Strong active voice: utilized power verbs ({', '.join(action_verbs_found[:4])}).")
    elif action_verbs_found:
        score += 3.0
        suggestions.append("Begin every bullet point with a decisive action verb (e.g. 'Architected', 'Engineered', 'Optimized', 'Streamlined').")
    else:
        suggestions.append("Start bullet points with strong action verbs rather than passive phrases like 'Responsible for' or 'Helped with'.")

    # 7. Check for weak project descriptions
    for p in valid_proj:
        desc_words = len(p.get("description", "").split())
        if desc_words < 15:
            suggestions.append(f"Project '{p.get('title')}' has a very brief description ({desc_words} words). Describe your role, tech stack, and key achievement.")

    # Clamp score
    final_score = round(min(100.0, max(0.0, score)), 1)

    # Determine Rating
    if final_score >= 88:
        rating = "Outstanding"
        rating_color = "#10B981"  # Emerald
        badge_text = "ATS Ready & Top Tier"
    elif final_score >= 72:
        rating = "Strong"
        rating_color = "#38BDF8"  # Cyan/Sky
        badge_text = "Good ATS Alignment"
    elif final_score >= 55:
        rating = "Good"
        rating_color = "#FBBF24"  # Amber
        badge_text = "Room for Improvement"
    else:
        rating = "Needs Improvement"
        rating_color = "#F43F5E"  # Rose
        badge_text = "Critical Updates Needed"

    # 8. Target Role ATS Keyword Guidance
    role_advice = {}
    if target_role and target_role in ROLE_RECOMMENDATIONS:
        rec_skills = ROLE_RECOMMENDATIONS[target_role]
        present_set = {s.lower() for s in detected_skills}
        matching = [s for s in rec_skills if s.lower() in present_set]
        missing = [s for s in rec_skills if s.lower() not in present_set]
        role_advice = {
            "target_role": target_role,
            "recommended": rec_skills,
            "matching": matching,
            "missing": missing,
            "coverage_pct": round((len(matching) / len(rec_skills)) * 100, 1) if rec_skills else 0
        }

    return {
        "score": final_score,
        "rating": rating,
        "rating_color": rating_color,
        "badge_text": badge_text,
        "strengths": strengths,
        "suggestions": suggestions,
        "critical_missing": critical_missing,
        "metrics_found": metrics_detected,
        "action_verbs_found": action_verbs_found,
        "detected_skills": detected_skills,
        "role_advice": role_advice
    }
