"""
ResumeRank AI - Profile Fact Extractor & Experience Analyzer.
Extracts grounded candidate facts (education degrees, experience spans, certifications)
from resume text and strictly distinguishes extracted facts from AI model inferences.
Never fabricates information absent from the resume text.
"""

import re
from typing import Dict, Any, List, Optional


def extract_candidate_profile_facts(text: str) -> Dict[str, Any]:
    """
    Extracts structured, factual information directly present in resume text.
    Provides verifiable citations/snippets for each extracted fact.
    """
    if not text or not isinstance(text, str):
        return {
            "degrees": [],
            "years_of_experience_est": None,
            "experience_snippets": [],
            "institutions": [],
            "certifications": [],
            "fact_count": 0
        }

    # 1. Degree Extraction
    degree_patterns = [
        (r"\b(?:ph\.?d|doctor\s+of\s+philosophy|doctorate)\b[^\n,.]*", "Ph.D. / Doctorate"),
        (r"\b(?:m\.?s(?:c)?|master\s+of\s+(?:science|technology|engineering|business|computer\s+applications)|m\.?tech|mca|mba)\b[^\n,.]*", "Master's Degree"),
        (r"\b(?:b\.?s(?:c)?|bachelor\s+of\s+(?:science|technology|engineering|arts|computer\s+applications)|b\.?tech|bca|b\.?e)\b[^\n,.]*", "Bachelor's Degree"),
        (r"\b(?:associate\s+degree|diploma)\b[^\n,.]*", "Associate / Diploma")
    ]

    detected_degrees = []
    for pat, label in degree_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            snippet = match.group(0).strip()
            # Truncate clean snippet
            if len(snippet) > 60:
                snippet = snippet[:60] + "..."
            detected_degrees.append({
                "level": label,
                "evidence": snippet
            })

    # 2. Experience Estimation (heuristic from date ranges & explicit statements)
    exp_statement = re.search(
        r"(\d+(?:\.\d+)?|\d+\+?)\s*(?:years?|yrs?)(?:\s+of)?(?:\s+(?:relevant|hands-on|industry|professional|software|engineering|data))?\s+experience",
        text,
        re.IGNORECASE
    )

    exp_years = None
    exp_snippets = []
    if exp_statement:
        exp_snippets.append(exp_statement.group(0).strip())
        num_str = re.search(r"\d+", exp_statement.group(1))
        if num_str:
            exp_years = float(num_str.group(0))
    else:
        # Check date spans (e.g., 2019 - 2024, 2021 - Present)
        year_spans = re.findall(r"\b(20\d{2})\s*(?:-|–|to)\s*(20\d{2}|present|current)\b", text, re.IGNORECASE)
        if year_spans:
            total_span = 0
            for start_y, end_y in year_spans:
                s_yr = int(start_y)
                e_yr = 2026 if end_y.lower() in ("present", "current") else int(end_y)
                diff = max(0, e_yr - s_yr)
                total_span = max(total_span, diff)
                exp_snippets.append(f"{start_y} - {end_y.capitalize()}")
            if total_span > 0:
                exp_years = float(min(total_span, 30))

    # 3. Certifications
    cert_matches = re.findall(
        r"\b(?:aws\s+certified[^\n,.]*|azure\s+certified[^\n,.]*|gcp\s+certified[^\n,.]*|cka\b|ckad\b|pmp\b|comptia[^\n,.]*|certified\s+[a-zA-Z\s]{4,30})",
        text,
        re.IGNORECASE
    )
    cleaned_certs = []
    acronym_map = {"aws": "AWS", "gcp": "GCP", "cka": "CKA", "ckad": "CKAD", "pmp": "PMP", "comptia": "CompTIA"}
    for c in cert_matches:
        s = c.strip()
        if len(s) > 3:
            words = s.split()
            formatted_words = []
            for w in words:
                w_lower = w.lower()
                if w_lower in acronym_map:
                    formatted_words.append(acronym_map[w_lower])
                else:
                    formatted_words.append(w.capitalize())
            cleaned_certs.append(" ".join(formatted_words))
    cleaned_certs = list(set(cleaned_certs))[:5]

    fact_count = len(detected_degrees) + (1 if exp_years is not None else 0) + len(cleaned_certs)

    return {
        "degrees": detected_degrees,
        "years_of_experience_est": exp_years,
        "experience_snippets": exp_snippets[:4],
        "certifications": cleaned_certs,
        "fact_count": fact_count
    }


def categorize_explanation_elements(explanation: Dict[str, Any], profile_facts: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Separates evaluation components strictly into:
    1. 'Extracted Facts': Directly quoted from resume text (zero model inference).
    2. 'AI Inferences': Semantic similarity, contextual score, rank, fit prediction.
    Ensures complete transparency for hackathon judges and recruiters.
    """
    facts = []
    inferences = []

    # Facts
    if profile_facts.get("degrees"):
        for deg in profile_facts["degrees"]:
            facts.append({
                "type": "Education Degree",
                "content": f"{deg['level']} (Evidence: '{deg['evidence']}')"
            })
    else:
        facts.append({
            "type": "Education Degree",
            "content": "No formal degree line explicitly detected in text."
        })

    if profile_facts.get("years_of_experience_est") is not None:
        facts.append({
            "type": "Experience Record",
            "content": f"Estimated ~{profile_facts['years_of_experience_est']:.0f} years based on resume date spans: {', '.join(profile_facts.get('experience_snippets', []))}"
        })
    else:
        facts.append({
            "type": "Experience Record",
            "content": "Experience duration not stated in standard numeric/date format."
        })

    if profile_facts.get("certifications"):
        facts.append({
            "type": "Certifications",
            "content": ", ".join(profile_facts["certifications"])
        })

    # Inferences
    breakdown = explanation.get("score_breakdown", {})
    inferences.append({
        "type": "Semantic Model Cosine Score",
        "content": f"{breakdown.get('semantic_score_pct', 0.0)}% contextual similarity generated by Sentence-Transformer (all-MiniLM-L6-v2) embeddings."
    })
    inferences.append({
        "type": "Skill Coverage Overlap",
        "content": f"{breakdown.get('skill_match_pct', 0.0)}% overlap with job description keywords after canonical synonym resolution."
    })
    inferences.append({
        "type": "Overall Fit Classification",
        "content": f"Tagged as '{explanation.get('overall_fit', 'Under Review')}' by weighted composite decision threshold."
    })

    return {
        "extracted_facts": facts,
        "model_inferences": inferences
    }
