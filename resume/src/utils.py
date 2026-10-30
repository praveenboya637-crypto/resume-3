"""
AI Resume Screening and Job Matching System
Utility helpers: CSV reports, file validation, metrics formatting, and sample resume generation.
"""

import io
import os
from typing import List, Dict, Any, Tuple
import pandas as pd


import re


def sanitize_filename(filename: str) -> str:
    """
    Safely sanitizes filenames by removing directory paths and special characters.
    """
    base = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
    return clean or "document"


def _sanitize_csv_cell(val: Any) -> Any:
    """
    Prevents CSV formula injection by quoting cells that begin with formula operators.
    """
    if isinstance(val, str) and val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + val
    return val


def generate_csv_report(ranked_candidates: List[Dict[str, Any]], jd_title: str = "Job Matching Report") -> str:
    """
    Generates a comprehensive CSV report string for export and download.
    Includes scores, matched/missing skills, verified evidence, formula breakdowns, and improvement tips.
    """
    records = []
    for c in ranked_candidates:
        expl = c.get("explanation", {})
        breakdown = expl.get("score_breakdown", {})
        suggestions = expl.get("actionable_suggestions", [])
        reviews = expl.get("review_needed_requirements", [])

        records.append({
            "Rank": _sanitize_csv_cell(c.get("rank", "-")),
            "Candidate / Filename": _sanitize_csv_cell(c.get("candidate_name", "Unknown")),
            "Status": _sanitize_csv_cell(c.get("status", "Unknown")),
            "Overall Match (%)": c.get("composite_score", 0.0),
            "Semantic Sim (%)": c.get("semantic_score_pct", 0.0),
            "Skill Match (%)": c.get("skill_match_pct", 0.0),
            "Matched Skills Count": len(c.get("matched_skills", [])),
            "Missing Skills Count": len(c.get("missing_skills", [])),
            "Decision Recommendation": _sanitize_csv_cell(
                "Shortlisted" if c.get("is_shortlisted") else ("Under Review" if c.get("status") == "Processed" else "Failed / Unreadable File")
            ),
            "Score Calculation Formula": _sanitize_csv_cell(breakdown.get("formula", "")),
            "Matched Skills List": _sanitize_csv_cell(" | ".join(c.get("matched_skills", []))),
            "Missing Skills List": _sanitize_csv_cell(" | ".join(c.get("missing_skills", []))),
            "Additional Skills List": _sanitize_csv_cell(" | ".join(c.get("additional_skills", []))),
            "Improvement Suggestions": _sanitize_csv_cell(" | ".join(suggestions)),
            "Review Needed in Interview": _sanitize_csv_cell(" | ".join(reviews)),
            "Overall Fit Category": _sanitize_csv_cell(expl.get("overall_fit", "")),
            "Candidate Email": _sanitize_csv_cell(c.get("metadata", {}).get("email", "")),
            "Word Count": c.get("metadata", {}).get("word_count", 0),
        })

    df = pd.DataFrame(records)
    return df.to_csv(index=False)


def validate_job_description(jd_text: str) -> Tuple[bool, str]:
    """
    Validates the job description input.
    """
    if not jd_text or not jd_text.strip():
        return False, "Job description cannot be empty. Please enter or paste the job requirements."

    words = jd_text.strip().split()
    if len(words) < 20:
        return False, f"Job description is too brief ({len(words)} words). Please provide at least 20 words for meaningful semantic evaluation."

    return True, "Valid"


def validate_uploaded_files(uploaded_files: list) -> Tuple[bool, List[str]]:
    """
    Validates uploaded resume files for type and count.
    """
    if not uploaded_files:
        return False, ["Please upload at least one resume (PDF or DOCX)."]

    allowed_exts = {".pdf", ".docx"}
    errors = []

    for f in uploaded_files:
        fname = getattr(f, "name", str(f))
        _, ext = os.path.splitext(fname.lower())
        if ext not in allowed_exts:
            errors.append(f"'{fname}' has an unsupported extension ({ext}). Only .pdf and .docx are supported.")

    if errors:
        return False, errors
    return True, []


def create_sample_files(target_dir: str):
    """
    Creates realistic sample resumes (both PDF and DOCX) in the target directory
    so the user or evaluator can test the entire pipeline with a single click.
    """
    import pymupdf  # PyMuPDF
    import docx

    os.makedirs(target_dir, exist_ok=True)

    # 1. Candidate 1: Alex Rivera (High Match for AI / ML Engineer) - PDF
    pdf_path_1 = os.path.join(target_dir, "Alex_Rivera_AI_Engineer.pdf")
    if not os.path.exists(pdf_path_1):
        doc1 = pymupdf.open()
        page1 = doc1.new_page()
        text_1 = """ALEX RIVERA
Email: alex.rivera@example.com | Phone: (555) 019-2834 | San Francisco, CA
LinkedIn: linkedin.com/in/alex-rivera-ai | GitHub: github.com/alexrivera-ai

PROFESSIONAL SUMMARY
Results-driven AI & Machine Learning Engineer with 4+ years of hands-on experience designing, training, and deploying deep learning models and NLP applications. Proven expertise in PyTorch, Scikit-Learn, Transformers, and Retrieval-Augmented Generation (RAG). Successfully deployed containerized microservices reducing inference latency by 42%.

TECHNICAL SKILLS
- Programming Languages: Python, SQL, C++, Bash
- AI / Machine Learning: PyTorch, TensorFlow, Scikit-Learn, Deep Learning, NLP, Transformers, Hugging Face, LLMs, RAG, LangChain, Vector Databases, Computer Vision, OpenCV
- Cloud & MLOps: AWS, Docker, Kubernetes, FastAPI, REST APIs, CI/CD, GitHub Actions, Linux
- Databases & Tools: PostgreSQL, MongoDB, Redis, Git, Unit Testing, pytest, Agile, Scrum

PROFESSIONAL EXPERIENCE
Senior Machine Learning Engineer | NeuralScale Technologies (2022 - Present)
- Architected enterprise RAG system using LangChain, Hugging Face Transformers, and PyTorch, increasing document search accuracy by 38%.
- Developed and deployed high-throughput FastAPI inference microservices on AWS EKS using Docker and Kubernetes.
- Automated ML model training and validation with CI/CD pipelines via GitHub Actions and pytest.
- Mentored junior engineers, led weekly agile sprints, and conducted structured code reviews.

Machine Learning Developer | DataCore Solutions (2020 - 2022)
- Built predictive customer analytics pipelines using Python, Pandas, NumPy, and Scikit-Learn across 2.5M records.
- Deployed REST APIs using Flask and Docker on AWS EC2, handling 15,000 requests per minute.
- Optimized database queries in PostgreSQL and Redis, decreasing response times by 30%.

EDUCATION
B.S. in Computer Science | University of California, Berkeley (2016 - 2020)
"""
        page1.insert_textbox(pymupdf.Rect(50, 50, 550, 780), text_1, fontsize=9.5, fontname="helv")
        doc1.save(pdf_path_1)
        doc1.close()

    # 2. Candidate 2: Priya Sharma (High Match for Full-Stack Developer) - DOCX
    docx_path_2 = os.path.join(target_dir, "Priya_Sharma_FullStack.docx")
    if not os.path.exists(docx_path_2):
        doc2 = docx.Document()
        doc2.add_heading("Priya Sharma", level=0)
        doc2.add_paragraph("Email: priya.sharma@example.com | Phone: (555) 345-6789 | Bengaluru, India\n"
                           "LinkedIn: linkedin.com/in/priyasharma-dev | GitHub: github.com/priyasharma-code")
        
        doc2.add_heading("Professional Summary", level=1)
        doc2.add_paragraph(
            "Versatile Full-Stack Web Developer with 3.5 years of experience engineering scalable web platforms. "
            "Expert in React, TypeScript, Next.js, Python (FastAPI/Django), and PostgreSQL. Passionate about responsive UI/UX, "
            "RESTful microservices, and continuous deployment."
        )

        doc2.add_heading("Technical Skills", level=1)
        doc2.add_paragraph(
            "Languages: Python, JavaScript, TypeScript, HTML5, CSS3, SQL\n"
            "Frontend: React, Next.js, Redux, Tailwind CSS, Bootstrap\n"
            "Backend: FastAPI, Django, Node.js, Express, REST APIs, Microservices, WebSockets\n"
            "Databases: PostgreSQL, MySQL, Redis, MongoDB\n"
            "DevOps & Tools: Docker, Git, GitHub Actions, Linux, Nginx, Agile, Scrum, Unit Testing"
        )

        doc2.add_heading("Work Experience", level=1)
        doc2.add_heading("Lead Full-Stack Developer | CloudSphere Innovations (2022 - Present)", level=2)
        doc2.add_paragraph(
            "- Spearheaded development of core SaaS platform using React, TypeScript, and FastAPI, serving 120,000 monthly active users.\n"
            "- Designed scalable PostgreSQL schema with Redis caching, cutting average API latency by 45%.\n"
            "- Containerized applications with Docker and established automated CI/CD testing pipelines on GitHub Actions.\n"
            "- Collaborated closely with product managers and designers in bi-weekly Agile sprints."
        )

        doc2.add_heading("Full-Stack Developer | WebCraft Labs (2020 - 2022)", level=2)
        doc2.add_paragraph(
            "- Developed 15+ responsive client portals using React, HTML5, Tailwind CSS, and Node.js.\n"
            "- Integrated third-party payment gateways and authentication using JWT and OAuth2 REST APIs.\n"
            "- Improved unit test coverage to 88% using Jest and pytest."
        )

        doc2.add_heading("Education", level=1)
        doc2.add_paragraph("B.Tech in Information Technology | National Institute of Technology (2016 - 2020)")
        doc2.save(docx_path_2)

    # 3. Candidate 3: Jordan Lee (Data Scientist & Analyst) - PDF
    pdf_path_3 = os.path.join(target_dir, "Jordan_Lee_DataScientist.pdf")
    if not os.path.exists(pdf_path_3):
        doc3 = pymupdf.open()
        page3 = doc3.new_page()
        text_3 = """JORDAN LEE
Email: jordan.lee@example.com | Phone: (555) 987-6543 | Chicago, IL
LinkedIn: linkedin.com/in/jordanlee-ds | GitHub: github.com/jordanlee-data

PROFESSIONAL SUMMARY
Data Scientist and Analytics Specialist with 3 years of experience deriving strategic insights from high-dimensional datasets. Skilled in Python, Scikit-Learn, Pandas, NumPy, statistical hypothesis testing, and business intelligence dashboards in Tableau and Power BI.

CORE COMPETENCIES
- Programming & Analytics: Python, SQL, R, Pandas, NumPy, Scikit-Learn, Statistics, Hypothesis Testing, A/B Testing, Feature Engineering
- Machine Learning: Random Forest, XGBoost, Regression, Clustering, Predictive Modeling
- Visualization & BI: Tableau, Power BI, Plotly, Matplotlib, Seaborn, Excel
- Data Engineering & Cloud: PostgreSQL, Snowflake, BigQuery, ETL Pipelines, Git, Agile

PROFESSIONAL EXPERIENCE
Data Scientist | Vantage Analytics Group (2022 - Present)
- Developed customer churn prediction model using XGBoost and Scikit-Learn, achieving an AUC-ROC of 0.89 and saving $320K annually.
- Built automated ETL data pipelines querying Snowflake and PostgreSQL tables containing over 10M transaction records.
- Designed 12 executive dashboards in Tableau and Power BI monitored daily by C-suite executives.
- Conducted regular A/B experiments to evaluate conversion funnels and marketing campaigns.

Junior Data Analyst | MetroMetrics Corp (2021 - 2022)
- Cleaned and prepared complex datasets with Python (Pandas/NumPy) and SQL.
- Created monthly automated reporting decks and interactive charts using Plotly and Seaborn.
- Collaborated across marketing and product teams to define key performance indicators (KPIs).

EDUCATION
M.S. in Data Science & Statistics | Northwestern University (2019 - 2021)
B.S. in Mathematics | University of Illinois (2015 - 2019)
"""
        page3.insert_textbox(pymupdf.Rect(50, 50, 550, 780), text_3, fontsize=9.5, fontname="helv")
        doc3.save(pdf_path_3)
        doc3.close()

    # 4. Candidate 4: Sam Taylor (Junior Generalist / Low Match for specialized AI role) - PDF
    pdf_path_4 = os.path.join(target_dir, "Sam_Taylor_JuniorDev.pdf")
    if not os.path.exists(pdf_path_4):
        doc4 = pymupdf.open()
        page4 = doc4.new_page()
        text_4 = """SAM TAYLOR
Email: sam.taylor@example.com | Phone: (555) 432-1098 | Austin, TX

SUMMARY
Motivated Junior Web Developer and recent graduate passionate about frontend design, HTML/CSS, basic JavaScript, and introductory Python programming. Eager to contribute to collaborative software teams.

SKILLS
- Languages: HTML, CSS, JavaScript, Basic Python
- Tools: Git, GitHub, VS Code, Figma
- Soft Skills: Communication, Teamwork, Time Management

EXPERIENCE
Frontend Web Intern | Local Digital Agency (2023 - 2024)
- Built landing pages for local businesses using HTML5, CSS3, and JavaScript.
- Assisted with website maintenance and bug fixing on WordPress sites.
- Collaborated with senior designers to refine UI mockups in Figma.

PROJECTS
Personal Portfolio Website
- Designed and published a mobile-responsive portfolio site using HTML, CSS, and basic JavaScript.
Weather Tracker App
- Developed simple client-side application fetching weather data from public open APIs.

EDUCATION
B.A. in Digital Media & Web Design | State College (2020 - 2024)
"""
        page4.insert_textbox(pymupdf.Rect(50, 50, 550, 780), text_4, fontsize=9.5, fontname="helv")
        doc4.save(pdf_path_4)
        doc4.close()
