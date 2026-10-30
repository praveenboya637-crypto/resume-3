"""
AI Resume Screening and Job Matching System
Candidate Ranking, Transparent Score Breakdown, and Explainable AI Recommendation Engine.
"""

import re
from typing import List, Dict, Any, Tuple
import pandas as pd
from src.constants import (
    DEFAULT_SEMANTIC_WEIGHT,
    DEFAULT_SKILL_WEIGHT,
    DEFAULT_SHORTLIST_THRESHOLD
)
from src.skills_extractor import analyze_skill_gap


def generate_explainable_feedback(
    candidate_name: str,
    composite_score: float,
    semantic_score_pct: float,
    skill_gap: Dict[str, Any],
    metadata: Dict[str, Any],
    text: str,
    w_sem: float = DEFAULT_SEMANTIC_WEIGHT,
    w_ski: float = DEFAULT_SKILL_WEIGHT
) -> Dict[str, Any]:
    """
    Generates transparent, human-readable explanations, score breakdown math,
    and grounded resume optimization suggestions based strictly on actual comparison results.
    Never invents or hallucinates qualifications the candidate does not have.
    """
    strengths = []
    gap_warnings = []
    actionable_suggestions = []
    review_needed_requirements = []

    matched_skills = skill_gap.get("matched_skills", [])
    missing_skills = skill_gap.get("missing_skills", [])
    additional_skills = skill_gap.get("additional_skills", [])
    matched_evidence = skill_gap.get("matched_evidence", {})
    skill_pct = skill_gap.get("skill_match_percentage", 0.0)

    # 1. Semantic alignment evaluation
    if semantic_score_pct >= 75:
        strengths.append(
            f"Strong contextual alignment ({semantic_score_pct:.1f}%): The candidate's experience closely mirrors "
            "the core terminology, responsibilities, and domain requirements of the job description."
        )
    elif semantic_score_pct >= 55:
        strengths.append(
            f"Moderate contextual alignment ({semantic_score_pct:.1f}%): The resume shares related domain vocabulary, "
            "though specialized project depth in certain role areas may be underrepresented."
        )
    else:
        gap_warnings.append(
            f"Lower contextual similarity ({semantic_score_pct:.1f}%): The overall language and project descriptions "
            "diverge noticeably from the target role's core expectations."
        )

    # 2. Hard skills match evaluation with job-related evidence
    if matched_skills:
        top_matched = ", ".join(matched_skills[:6])
        strengths.append(f"Demonstrated Key Skills: Successfully verified in resume: {top_matched}.")
    else:
        gap_warnings.append("No primary technical skills from the job description were directly identified.")

    # 3. Missing skills diagnosis & review requirements
    if missing_skills:
        top_missing = ", ".join(missing_skills[:6])
        gap_warnings.append(f"Skill Deficits: Missing key role requirements: {top_missing}.")
        actionable_suggestions.append(
            f"Add Targeted Experience: If you possess practical experience with {top_missing}, explicitly highlight "
            "them in your 'Technical Skills' and 'Key Projects' sections using standard terminology."
        )
        for s in missing_skills[:8]:
            review_needed_requirements.append(
                f"{s}: Not evidenced in resume text. Assess candidate familiarity during technical interview."
            )
    else:
        strengths.append("100% Skill Coverage: Candidate matches all recognized target technical skills in the job specification!")

    # 4. Bonus/Additional skills
    if additional_skills:
        top_bonus = ", ".join(additional_skills[:4])
        strengths.append(f"Versatility / Bonus Competencies: Offers additional skills not strictly requested: {top_bonus}.")

    # 5. Quantifiable metrics & impact check
    quant_matches = re.findall(r"\b(\d+[%kKmM]?|\$\d+)\b", text)
    if len(quant_matches) < 4:
        actionable_suggestions.append(
            "Quantify Achievements: Include specific numerical metrics (e.g., 'improved model inference speed by 35%', "
            "'reduced API latency by 120ms', 'scaled service to 50k users'). Numerical results substantially increase recruiter engagement."
        )
    else:
        strengths.append("Impact-Oriented: Resume demonstrates quantifiable outcomes and metric-driven accomplishments.")

    # 6. Length & density heuristics
    word_count = metadata.get("word_count", 0)
    if word_count < 150:
        actionable_suggestions.append(
            "Expand Technical Depth: The resume is concise (< 150 words). Elaborate on past projects, "
            "architectural choices, and libraries used to improve searchability."
        )
    elif word_count > 1200:
        actionable_suggestions.append(
            "Condense for Scannability: The resume exceeds 1,200 words. Consider streamlining older roles to keep "
            "the focus sharp on the most relevant, recent technical contributions."
        )

    # 7. Overall qualification category (Decision-support alignment estimate)
    if composite_score >= 80:
        overall_fit = "🌟 Excellent Match — High Textual Alignment Estimate"
    elif composite_score >= 65:
        overall_fit = "✅ Good Match — Meets Core Role Requirements"
    elif composite_score >= 50:
        overall_fit = "⚠️ Moderate Match — Relevant Foundation with Specific Skill Gaps"
    else:
        overall_fit = "❌ Low Match — Low Textual Alignment with Target Specification"

    # 8. Score Calculation Breakdown Explanation
    score_breakdown = {
        "formula": f"({semantic_score_pct:.1f}% × {w_sem:.2f}) + ({skill_pct:.1f}% × {w_ski:.2f}) = {composite_score:.1f}%",
        "semantic_contribution": round(semantic_score_pct * w_sem, 1),
        "skill_contribution": round(skill_pct * w_ski, 1),
        "semantic_weight_pct": round(w_sem * 100, 1),
        "skill_weight_pct": round(w_ski * 100, 1),
        "interpretation": "Decision-support matching estimate indicating contextual semantic and keyword alignment."
    }

    return {
        "overall_fit": overall_fit,
        "strengths": strengths,
        "gap_warnings": gap_warnings,
        "actionable_suggestions": actionable_suggestions,
        "review_needed_requirements": review_needed_requirements,
        "matched_evidence": matched_evidence,
        "score_breakdown": score_breakdown
    }


def rank_resumes(
    parsed_resumes: List[Dict[str, Any]],
    jd_text: str,
    semantic_similarities: List[float],
    semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
    skill_weight: float = DEFAULT_SKILL_WEIGHT,
    shortlist_threshold: float = DEFAULT_SHORTLIST_THRESHOLD
) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    """
    Ranks parsed resumes against a job description using a transparent composite score
    combining semantic embedding similarity and keyword skill overlap.
    
    Returns:
        (ranked_candidates_list, summary_dataframe)
    """
    candidates = []

    # Normalize weights
    total_w = semantic_weight + skill_weight
    w_sem = (semantic_weight / total_w) if total_w > 0 else 0.5
    w_ski = (skill_weight / total_w) if total_w > 0 else 0.5

    for i, res in enumerate(parsed_resumes):
        filename = res.get("filename", f"Candidate_{i+1}")
        clean_text = res.get("clean_text", "")
        metadata = res.get("metadata", {})
        status = res.get("status", "unknown")

        if status != "success" or not clean_text:
            candidates.append({
                "rank": None,
                "candidate_name": filename,
                "status": "Failed / Empty",
                "composite_score": 0.0,
                "semantic_score_pct": 0.0,
                "skill_match_pct": 0.0,
                "matched_skills": [],
                "missing_skills": [],
                "additional_skills": [],
                "matched_evidence": {},
                "skill_gap": {},
                "explanation": {
                    "overall_fit": "Invalid / Unreadable File",
                    "strengths": [],
                    "gap_warnings": [res.get("error_message", "File could not be parsed.")],
                    "actionable_suggestions": ["Upload a non-empty PDF or DOCX file containing selectable or OCR-readable text."],
                    "review_needed_requirements": [],
                    "matched_evidence": {},
                    "score_breakdown": {
                        "formula": "0.0% (Unreadable / Empty File)",
                        "semantic_contribution": 0.0,
                        "skill_contribution": 0.0,
                        "semantic_weight_pct": round(w_sem * 100, 1),
                        "skill_weight_pct": round(w_ski * 100, 1),
                        "interpretation": "Document contained 0 extractable characters."
                    }
                },
                "is_shortlisted": False,
                "metadata": metadata,
                "error": res.get("error_message")
            })
            continue

        # 1. Semantic score percentage
        sem_sim = semantic_similarities[i] if i < len(semantic_similarities) else 0.0
        sem_score_pct = round(sem_sim * 100, 1)

        # 2. Skill gap analysis
        skill_gap = analyze_skill_gap(clean_text, jd_text)
        skill_pct = skill_gap["skill_match_percentage"]

        # 3. Composite score calculation
        # If JD has no recognized skills in taxonomy, score is determined 100% by semantic similarity
        if len(skill_gap.get("all_jd_skills", [])) == 0:
            composite = sem_score_pct
        else:
            composite = round((sem_score_pct * w_sem) + (skill_pct * w_ski), 1)

        composite = max(0.0, min(100.0, composite))
        is_shortlisted = composite >= shortlist_threshold

        # 4. Explainable AI feedback & evidence
        explanation = generate_explainable_feedback(
            candidate_name=filename,
            composite_score=composite,
            semantic_score_pct=sem_score_pct,
            skill_gap=skill_gap,
            metadata=metadata,
            text=clean_text,
            w_sem=w_sem,
            w_ski=w_ski
        )

        candidates.append({
            "candidate_name": filename,
            "composite_score": composite,
            "semantic_score_pct": sem_score_pct,
            "skill_match_pct": skill_pct,
            "matched_skills": skill_gap["matched_skills"],
            "missing_skills": skill_gap["missing_skills"],
            "additional_skills": skill_gap["additional_skills"],
            "matched_evidence": skill_gap.get("matched_evidence", {}),
            "skill_gap": skill_gap,
            "explanation": explanation,
            "is_shortlisted": is_shortlisted,
            "metadata": metadata,
            "status": "Processed",
            "error": None
        })

    # Sort valid candidates by composite score descending
    valid_candidates = [c for c in candidates if c["status"] == "Processed"]
    failed_candidates = [c for c in candidates if c["status"] != "Processed"]

    valid_candidates.sort(key=lambda x: x["composite_score"], reverse=True)

    # Assign 1-indexed ranks
    for rank_idx, c in enumerate(valid_candidates, 1):
        c["rank"] = rank_idx

    for c in failed_candidates:
        c["rank"] = "-"

    ranked_all = valid_candidates + failed_candidates

    # Build summary pandas DataFrame
    table_rows = []
    for c in ranked_all:
        table_rows.append({
            "Rank": c["rank"],
            "Candidate / File": c["candidate_name"],
            "Overall Match (%)": c["composite_score"],
            "Semantic Sim (%)": c["semantic_score_pct"],
            "Skill Match (%)": c["skill_match_pct"],
            "Matched Skills Count": len(c["matched_skills"]),
            "Missing Skills Count": len(c["missing_skills"]),
            "Decision Support": "⭐ Shortlisted" if c["is_shortlisted"] else ("⚠️ Under Review" if c["status"] == "Processed" else "❌ Failed"),
            "Score Calculation": c["explanation"]["score_breakdown"]["formula"],
            "Matched Skills": ", ".join(c["matched_skills"][:5]) + ("..." if len(c["matched_skills"]) > 5 else ""),
            "Missing Skills": ", ".join(c["missing_skills"][:5]) + ("..." if len(c["missing_skills"]) > 5 else "")
        })

    df = pd.DataFrame(table_rows)
    return ranked_all, df
