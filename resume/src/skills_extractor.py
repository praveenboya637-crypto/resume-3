"""
AI Resume Screening and Job Matching System
Skill Extraction, Synonym Harmonization, and Evidence-Based Gap Analysis Engine.
"""

import re
from typing import Dict, List, Set, Any, Optional
from src.constants import SKILL_TAXONOMY, ALL_SKILLS_LOOKUP, SPECIAL_DISPLAYS, SKILL_SYNONYMS


def _match_contextual_c(text_lower: str) -> bool:
    """Matches C programming language while avoiding false positives like 'Grade C' or 'Section C'."""
    # Explicit phrases
    if re.search(r"\b(?:c\s*programming|c\s*language|ansi\s*c|embedded\s*c|c\s*developer|c\s*compiler|c\s*standard)\b", text_lower):
        return True
    # C paired with C++ or C#
    if re.search(r"\b(?:c\s*/\s*c\+\+|c\+\+\s*/\s*c|c\s*/\s*c\#|c\#\s*/\s*c)\b", text_lower):
        return True
    # In lists of programming languages
    lang_group = r"(?:c\+\+|c\#|python|java|assembly|rust|sql|golang|r|javascript|typescript)"
    if re.search(rf"\bc[,\s/]+{lang_group}(?:[\s,;/().]|$)", text_lower) or re.search(rf"(?:^|\s){lang_group}[,\s/]+c\b", text_lower):
        return True
    # In a technical skills header line, e.g. "Languages: C, Python"
    if re.search(r"(?:^|\n|\b)(?:technical\s+)?(?:languages?|skills|technologies)\s*:[^\n]*\b[Cc]\b", text_lower):
        return True
    return False


def _match_contextual_r(text_lower: str) -> bool:
    """Matches R statistical programming while avoiding false positives like middle initials (John R. Smith)."""
    # Explicit phrases
    if re.search(r"\b(?:r\s*programming|r\s*language|r\s*scripting|r\s*shiny|r\s*markdown|r\s*developer|r\s*packages)\b", text_lower):
        return True
    # RStudio
    if re.search(r"\br[\-\s]?studio\b", text_lower):
        return True
    # Paired with Python or SQL (e.g. R/Python or Python/R)
    if re.search(r"\b(?:r\s*/\s*python|python\s*/\s*r|r\s*/\s*sql|sql\s*/\s*r)\b", text_lower):
        return True
    # In statistical / data science lists
    stat_group = r"(?:python|sql|sas|matlab|spss|stata|pandas|numpy|julia)"
    if re.search(rf"\br[,\s/]+{stat_group}(?:[\s,;/().]|$)", text_lower) or re.search(rf"(?:^|\s){stat_group}[,\s/]+r\b", text_lower):
        return True
    # In a technical skills header line, e.g. "Languages: R, Python"
    if re.search(r"(?:^|\n|\b)(?:technical\s+)?(?:languages?|skills|technologies)\s*:[^\n]*\b[Rr]\b", text_lower):
        return True
    return False


def _match_contextual_go(text_lower: str) -> bool:
    """Matches Go/Golang programming language while avoiding common English verbs ('go to', 'go through')."""
    # Explicit golang or phrases
    if re.search(r"\bgolang\b", text_lower):
        return True
    if re.search(r"\bgo\s+(?:lang|language|programming|developer|engineer|backend|microservices|code)\b", text_lower):
        return True
    if re.search(r"\b(?:programming in|developed in|written in|experience with|proficient in|built with|using)\s+go\b", text_lower):
        return True
    # In lists of programming languages
    lang_group = r"(?:python|java|rust|c\+\+|c\#|ruby|sql|kotlin|scala|php|c)"
    if re.search(rf"\bgo[,\s/]+{lang_group}(?:[\s,;/().]|$)", text_lower) or re.search(rf"(?:^|\s){lang_group}[,\s/]+go\b", text_lower):
        return True
    # In a technical skills header line
    if re.search(r"(?:^|\n|\b)(?:technical\s+)?(?:languages?|skills|technologies)\s*:[^\n]*\b[Gg]o\b", text_lower):
        return True
    return False


def extract_skills_from_text(text: str) -> Dict[str, Any]:
    """
    Extracts recognized skills from text based on our curated taxonomy and synonym mappings.
    Handles exact single words, multi-word phrases, and programming symbols (C++, C#, .NET).
    Prevents false positives on single letters (C, R) and common verbs (Go).
    
    Returns a dictionary:
    {
        "all_skills": List[str] (canonical lowercase),
        "display_skills": List[str] (formatted display names),
        "by_category": Dict[str, List[str]],
        "count": int
    }
    """
    if not text or not isinstance(text, str):
        return {"all_skills": [], "display_skills": [], "by_category": {}, "count": 0}

    # Lowercase text for matching, but keep characters like +, #, .
    text_lower = " " + text.lower() + " "
    # Replace punctuation separators with spaces for tokenization
    text_clean = re.sub(r"[,;:/\\()\[\]{}|<>!?*\"~]", " ", text_lower)
    text_clean = re.sub(r"[ ]{2,}", " ", text_clean)

    detected_skills: Set[str] = set()

    # 1. Match Taxonomy Skills (longest first)
    sorted_skills = sorted(ALL_SKILLS_LOOKUP.keys(), key=lambda s: len(s), reverse=True)

    for skill in sorted_skills:
        # Contextual single/short words to prevent false positives
        if skill == "c":
            if _match_contextual_c(text_lower):
                detected_skills.add("c")
            continue
        elif skill == "r":
            if _match_contextual_r(text_lower):
                detected_skills.add("r")
            continue
        elif skill in ["go", "golang"]:
            if _match_contextual_go(text_lower):
                detected_skills.add("golang")
            continue

        # Special boundary handling for symbols like C++, C#, .NET, ASP.NET
        if skill in ["c++", "c#"]:
            escaped = re.escape(skill)
            pattern = rf"(?:^|[\s,;/()\-]){escaped}(?:[\s,;/()\-:.]|$)"
            if re.search(pattern, text_lower):
                detected_skills.add(skill)
        elif skill in [".net", "asp.net"]:
            escaped = re.escape(skill)
            pattern = rf"(?:^|[\s,;/()\-]){escaped}(?:[\s,;/()\-:.]|$)"
            if re.search(pattern, text_lower):
                detected_skills.add(skill)
        else:
            # Multi-word or standard dictionary words with strict word boundaries
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, text_clean):
                detected_skills.add(skill)

    # 2. Match Synonyms and Alternate Phrasings
    for syn, canonical in SKILL_SYNONYMS.items():
        if canonical in detected_skills:
            continue
        # Symbol-aware matching for synonyms
        if "/" in syn or "+" in syn or "#" in syn or "." in syn:
            escaped = re.escape(syn)
            pattern = rf"(?:^|[\s,;/()\-]){escaped}(?:[\s,;/()\-:.]|$)"
            if re.search(pattern, text_lower):
                detected_skills.add(canonical)
        else:
            pattern = rf"\b{re.escape(syn)}\b"
            if re.search(pattern, text_clean):
                detected_skills.add(canonical)

    # Group detected skills by category
    by_category: Dict[str, List[str]] = {}
    display_list: List[str] = []

    for skill in sorted(detected_skills):
        meta = ALL_SKILLS_LOOKUP.get(skill, {"display": skill.title(), "category": "Other"})
        display_name = meta["display"]
        category = meta["category"]

        if category not in by_category:
            by_category[category] = []
        by_category[category].append(display_name)
        display_list.append(display_name)

    return {
        "all_skills": sorted(list(detected_skills)),
        "display_skills": sorted(display_list),
        "by_category": by_category,
        "count": len(detected_skills)
    }


def extract_skill_evidence(text: str, skill_canonical: str, max_chars: int = 140) -> Optional[str]:
    """
    Extracts the actual sentence or bullet point from the resume where a skill was evidenced.
    Provides verifiable, job-related evidence without hallucinating or inventing candidate qualifications.
    """
    if not text:
        return None

    # Determine all search variations for this skill (canonical + synonyms)
    variations = [skill_canonical]
    for syn, can in SKILL_SYNONYMS.items():
        if can == skill_canonical:
            variations.append(syn)

    # Break text into individual lines and sentences
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        line_lower = line.lower()
        for var in variations:
            if var in ["c++", "c#", ".net", "ci/cd"]:
                p = rf"(?:^|[\s,;/()\-]){re.escape(var)}(?:[\s,;/()\-:.]|$)"
            elif var in ["c", "r", "go"]:
                p = rf"\b{re.escape(var)}\b"
            else:
                p = rf"\b{re.escape(var)}\b"

            if re.search(p, line_lower):
                # Clean line (remove leading bullets or dashes)
                clean_line = re.sub(r"^[•\-\*\d\.\)\s]+", "", line).strip()
                if len(clean_line) > max_chars:
                    return clean_line[:max_chars - 3].strip() + "..."
                return clean_line

    return None


def analyze_skill_gap(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Performs comprehensive Skill Gap Analysis between a candidate resume and a job description.
    Extracts matched skills with verified textual evidence, missing requirements, and bonus competencies.
    
    Returns:
    - matched_skills: Skills in both JD and Resume.
    - missing_skills: Skills required by JD but missing in Resume.
    - additional_skills: Skills in Resume not required by JD (bonus competencies).
    - matched_evidence: Dictionary mapping matched skill -> verbatim resume snippet.
    - skill_match_percentage: Percentage of JD skills satisfied by candidate.
    - category_breakdown: Comparative breakdown by skill category.
    """
    jd_extracted = extract_skills_from_text(jd_text)
    resume_extracted = extract_skills_from_text(resume_text)

    jd_set = set(jd_extracted["all_skills"])
    resume_set = set(resume_extracted["all_skills"])

    matched_set = jd_set.intersection(resume_set)
    missing_set = jd_set - resume_set
    additional_set = resume_set - jd_set

    # Calculate match percentage
    if jd_set:
        skill_match_pct = round((len(matched_set) / len(jd_set)) * 100, 1)
    else:
        # If JD has no recognized skills in taxonomy, report 0.0 (composite score will fall back to semantic)
        skill_match_pct = 0.0

    # Format into display names
    def format_set(skill_set: Set[str]) -> List[str]:
        return sorted([ALL_SKILLS_LOOKUP.get(s, {}).get("display", s.title()) for s in skill_set])

    matched_display = format_set(matched_set)
    missing_display = format_set(missing_set)
    additional_display = format_set(additional_set)

    # Extract verified resume evidence for matched skills
    matched_evidence = {}
    for skill_can in matched_set:
        disp_name = ALL_SKILLS_LOOKUP.get(skill_can, {}).get("display", skill_can.title())
        ev = extract_skill_evidence(resume_text, skill_can)
        if ev:
            matched_evidence[disp_name] = ev

    # Category-level breakdown
    category_summary = {}
    all_categories = set(list(jd_extracted["by_category"].keys()) + list(resume_extracted["by_category"].keys()))

    for cat in sorted(all_categories):
        jd_skills_in_cat = [s for s in jd_set if ALL_SKILLS_LOOKUP.get(s, {}).get("category") == cat]
        matched_in_cat = [s for s in matched_set if ALL_SKILLS_LOOKUP.get(s, {}).get("category") == cat]
        missing_in_cat = [s for s in missing_set if ALL_SKILLS_LOOKUP.get(s, {}).get("category") == cat]

        category_summary[cat] = {
            "jd_count": len(jd_skills_in_cat),
            "matched_count": len(matched_in_cat),
            "missing_count": len(missing_in_cat),
            "matched_display": [ALL_SKILLS_LOOKUP.get(s, {}).get("display", s) for s in matched_in_cat],
            "missing_display": [ALL_SKILLS_LOOKUP.get(s, {}).get("display", s) for s in missing_in_cat]
        }

    return {
        "jd_skills_count": len(jd_set),
        "resume_skills_count": len(resume_set),
        "matched_count": len(matched_set),
        "missing_count": len(missing_set),
        "additional_count": len(additional_set),
        "skill_match_percentage": skill_match_pct,
        "matched_skills": matched_display,
        "missing_skills": missing_display,
        "additional_skills": additional_display,
        "matched_evidence": matched_evidence,
        "category_summary": category_summary,
        "all_jd_skills": jd_extracted["display_skills"],
        "all_resume_skills": resume_extracted["display_skills"]
    }
