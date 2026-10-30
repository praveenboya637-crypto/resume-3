"""
ResumeRank AI - Job Description Intelligence & Requirement Parser.
Analyzes job descriptions into Required vs Preferred skills, experience targets,
education expectations, and flags ambiguous or clichéd specifications.
Allows human recruiters to audit and edit criteria before screening.
"""

import re
from typing import Dict, Any, List, Set
from src.constants import ALL_SKILLS_LOOKUP, SKILL_TAXONOMY
from src.skills_extractor import extract_skills_from_text


# Clichés and ambiguous buzzwords in tech job descriptions
BUZZWORD_PATTERNS = [
    (r"\b(?:rockstar|rock\s*star)\b", "Vague buzzword: 'rockstar'. Replace with specific technical responsibilities."),
    (r"\b(?:ninja|wizard|guru|jedi)\b", "Overused informal slang. Deteriorates professional clarity."),
    (r"\b(?:wear\s+(?:many|multiple)\s+hats)\b", "Ambiguous scope: implies unconstrained or poorly defined role boundaries."),
    (r"\b(?:fast-paced|high-stress|pressure\s*cooker)\b", "Culture flag: indicates potential organizational burnout risks."),
    (r"\b(?:work\s+hard[,\s]+play\s+hard)\b", "Unclear work-life balance expectation."),
    (r"\b(?:self-starter\s+with\s+no\s+supervision)\b", "Potential onboarding deficit: implies lack of mentorship or documentation."),
    (r"\b(?:competitive\s+salary)\b", "Salary opacity: specify actual compensation band for transparency and fairness.")
]

def analyze_job_description(jd_text: str) -> Dict[str, Any]:
    """
    Performs comprehensive deep analysis of a job description.
    Extracts:
    - Required vs Preferred technical skills
    - Years of experience expectations
    - Education / degree prerequisites
    - Ambiguity, buzzword, and clarity audit
    - Readability metrics & recommendations
    """
    if not jd_text or not isinstance(jd_text, str):
        return {
            "required_skills": [],
            "preferred_skills": [],
            "all_extracted_skills": [],
            "experience_required": "Not specified",
            "education_required": "Not specified",
            "clarity_score": 0,
            "buzzwords_found": [],
            "clarity_warnings": ["Job description is empty."],
            "strengths": []
        }

    extracted = extract_skills_from_text(jd_text)
    all_skills = extracted.get("all_skills", [])
    display_skills = extracted.get("display_skills", [])
    
    # Map lowercase to display
    display_map = dict(zip(all_skills, display_skills))

    # Split text into sections if headers exist
    lines = jd_text.split("\n")
    current_section = "general"
    section_texts: Dict[str, List[str]] = {
        "required": [],
        "preferred": [],
        "responsibilities": [],
        "general": []
    }

    req_header_pattern = re.compile(
        r"(?:requirements?|qualifications?|must\s+have|minimum\s+qualifications?|what\s+you\s+need|basic\s+qualifications?)",
        re.IGNORECASE
    )
    pref_header_pattern = re.compile(
        r"(?:preferred|nice\s+to\s+have|bonus|plus|desired|optional|good\s+to\s+have)",
        re.IGNORECASE
    )
    resp_header_pattern = re.compile(
        r"(?:responsibilities|what\s+you(?:'ll|\s+will)\s+do|duties|the\s+role|about\s+the\s+job)",
        re.IGNORECASE
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Check if line looks like a header
        if len(stripped) < 60 and (stripped.endswith(":") or stripped.isupper() or stripped.startswith("#")):
            if pref_header_pattern.search(stripped):
                current_section = "preferred"
                continue
            elif req_header_pattern.search(stripped):
                current_section = "required"
                continue
            elif resp_header_pattern.search(stripped):
                current_section = "responsibilities"
                continue

        section_texts[current_section].append(stripped)

    # Extract skills by section
    required_text = " ".join(section_texts["required"])
    preferred_text = " ".join(section_texts["preferred"])
    
    req_skills_raw = extract_skills_from_text(required_text).get("all_skills", []) if required_text else []
    pref_skills_raw = extract_skills_from_text(preferred_text).get("all_skills", []) if preferred_text else []

    # If no explicit sections were parsed, intelligently segment based on proximity to phrases
    if not req_skills_raw and not pref_skills_raw:
        # Default heuristic: if fewer than 6 skills, all are required.
        # Otherwise, top 60% are marked required, remainder preferred.
        cutoff = max(1, int(len(all_skills) * 0.70))
        required_skills = [display_map.get(s, s.title()) for s in all_skills[:cutoff]]
        preferred_skills = [display_map.get(s, s.title()) for s in all_skills[cutoff:]]
    else:
        # Map to display
        req_set = set(req_skills_raw)
        pref_set = set(pref_skills_raw) - req_set
        
        # Remaining general skills go to required if reasonable
        for s in all_skills:
            if s not in req_set and s not in pref_set:
                req_set.add(s)

        required_skills = [display_map.get(s, s.title()) for s in req_set if s in display_map]
        preferred_skills = [display_map.get(s, s.title()) for s in pref_set if s in display_map]

    # 2. Extract Experience Requirements
    exp_matches = re.findall(
        r"(\d+(?:\s*(?:-|to)\s*\d+)?|\d+\+?)\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant|hands-on|industry|professional|practical|software|technical|direct))*\s+experience",
        jd_text,
        re.IGNORECASE
    )
    experience_required = f"{exp_matches[0]} years" if exp_matches else "Experience level not explicitly stated"

    # 3. Extract Education Requirements
    edu_patterns = [
        (r"\b(?:ph\.?d|doctorate)\b", "Ph.D. / Doctorate"),
        (r"\b(?:master'?s|m\.?s|m\.?tech|mca)\b", "Master's Degree (M.S. / M.Tech / MCA)"),
        (r"\b(?:bachelor'?s|b\.?s|b\.?tech|bca|b\.?e)\b", "Bachelor's Degree (B.S. / B.Tech / B.E.)"),
        (r"\b(?:diploma|associate'?s)\b", "Associate / Diploma")
    ]
    detected_edu = []
    for pat, label in edu_patterns:
        if re.search(pat, jd_text, re.IGNORECASE):
            detected_edu.append(label)
    education_required = ", ".join(detected_edu) if detected_edu else "Degree in Computer Science or equivalent practical experience"

    # 4. Ambiguity & Buzzword Audit
    buzzwords_found = []
    for pattern, warning in BUZZWORD_PATTERNS:
        matches = re.findall(pattern, jd_text, re.IGNORECASE)
        if matches:
            buzzwords_found.append({
                "term": matches[0],
                "warning": warning
            })

    clarity_warnings = []
    strengths = []
    clarity_score = 100

    word_count = len(jd_text.split())
    if word_count < 80:
        clarity_score -= 25
        clarity_warnings.append("Job description is very brief (< 80 words). May cause false similarity matches.")
    elif word_count > 150:
        strengths.append("Thorough role detail and contextual depth.")

    if not experience_required or "not explicitly" in experience_required.lower():
        clarity_score -= 10
        clarity_warnings.append("Seniority / minimum years of experience is not defined.")
    else:
        strengths.append(f"Clear seniority expectation: {experience_required}.")

    if len(all_skills) < 3:
        clarity_score -= 20
        clarity_warnings.append("Fewer than 3 technical skills detected. Screenings may rely disproportionately on generic text.")
    else:
        strengths.append(f"High technical precision: {len(all_skills)} specific skills mapped.")

    if buzzwords_found:
        clarity_score -= (len(buzzwords_found) * 8)
        clarity_warnings.append(f"Contains {len(buzzwords_found)} clichéd or vague terms that can deter top-tier talent.")

    clarity_score = max(20, min(100, clarity_score))

    return {
        "required_skills": sorted(list(set(required_skills))),
        "preferred_skills": sorted(list(set(preferred_skills))),
        "all_extracted_skills": display_skills,
        "experience_required": experience_required,
        "education_required": education_required,
        "clarity_score": clarity_score,
        "buzzwords_found": buzzwords_found,
        "clarity_warnings": clarity_warnings,
        "strengths": strengths,
        "word_count": word_count
    }
