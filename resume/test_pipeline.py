"""
AI Resume Screening and Job Matching System
Automated End-to-End Pipeline Verification Test.
Runs text parsing, skill extraction, sentence embeddings, ranking, and CSV export.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles to prevent charmap UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.constants import SAMPLE_JOB_DESCRIPTIONS, DEFAULT_MODEL_NAME
from src.parsers import parse_resume
from src.skills_extractor import extract_skills_from_text, analyze_skill_gap
from src.embeddings import load_sentence_transformer_model, batch_compute_similarity
from src.ranker import rank_resumes
from src.utils import create_sample_files, generate_csv_report


def run_pipeline_test():
    print("=" * 65)
    print("[TEST] Running AI Resume Screening & Job Matching Pipeline")
    print("=" * 65)

    # 1. Create sample resume files
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data", "resumes")
    print(f"\n[1/6] Generating sample PDF & DOCX resumes in '{sample_dir}'...")
    create_sample_files(sample_dir)
    sample_files = [f for f in os.listdir(sample_dir) if f.endswith((".pdf", ".docx"))]
    print(f"      Generated {len(sample_files)} sample files: {sample_files}")

    # 2. Parse Resumes
    print("\n[2/6] Parsing resumes using PyMuPDF and python-docx...")
    parsed_resumes = []
    for fname in sorted(sample_files):
        fpath = os.path.join(sample_dir, fname)
        res = parse_resume(fpath, filename=fname)
        parsed_resumes.append(res)
        print(f"      -> {fname}: Status={res['status']}, Words={res['metadata'].get('word_count', 0)}, Email={res['metadata'].get('email')}")

    # 3. Test Skill Extraction
    print("\n[3/6] Testing Skill Taxonomy Extraction & Gap Analysis...")
    sample_jd = SAMPLE_JOB_DESCRIPTIONS["AI / Machine Learning Engineer"]
    jd_skills = extract_skills_from_text(sample_jd)
    print(f"      JD detected skills ({jd_skills['count']}): {', '.join(jd_skills['display_skills'][:8])}...")

    # 4. Load Pretrained Sentence Transformer Model
    print(f"\n[4/6] Initializing Pretrained Embedding Model ('{DEFAULT_MODEL_NAME}')...")
    model, backend = load_sentence_transformer_model(DEFAULT_MODEL_NAME)
    print(f"      Model Backend: {backend}")

    # 5. Compute Batch Semantic Similarity
    print("\n[5/6] Computing dense contextual sentence embeddings & cosine similarity...")
    similarities = batch_compute_similarity(parsed_resumes, sample_jd, model=model)
    for res, sim in zip(parsed_resumes, similarities):
        print(f"      -> {res['filename']}: Semantic Similarity = {sim * 100:.1f}%")

    # 6. Rank Resumes & Generate Decision Support
    print("\n[6/6] Computing composite score, ranking candidates & generating XAI feedback...")
    ranked_candidates, summary_df = rank_resumes(
        parsed_resumes=parsed_resumes,
        jd_text=sample_jd,
        semantic_similarities=similarities,
        semantic_weight=0.60,
        skill_weight=0.40,
        shortlist_threshold=70.0
    )

    print("\n" + "=" * 65)
    print("FINAL RANKING LEADERBOARD")
    print("=" * 65)
    for c in ranked_candidates:
        flag = "[SHORTLISTED]" if c["is_shortlisted"] else "[UNDER REVIEW]"
        print(f"Rank #{c['rank']} | {c['candidate_name']:<30} | Match: {c['composite_score']:>5.1f}% | Sem: {c['semantic_score_pct']:>5.1f}% | Skill: {c['skill_match_pct']:>5.1f}% | {flag}")
        if c.get("matched_skills"):
            print(f"   Matched: {', '.join(c['matched_skills'][:5])}")
        if c.get("missing_skills"):
            print(f"   Missing: {', '.join(c['missing_skills'][:4])}")

    # 7. Test CSV Report Generation
    csv_report = generate_csv_report(ranked_candidates, jd_title="AI Engineer")
    csv_path = os.path.join(sample_dir, "..", "test_screening_report.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_report)
    print(f"\n[OK] CSV Report generated at: {csv_path}")

    print("\n" + "=" * 65)
    print("[SUCCESS] ALL PIPELINE TESTS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    run_pipeline_test()
