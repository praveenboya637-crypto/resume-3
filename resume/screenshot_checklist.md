# College Submission Screenshot Checklist
## AI Resume Screening and Job Matching System

To present a compelling project report and PowerPoint presentation, capture high-resolution screenshots from your live running Streamlit dashboard. Follow this step-by-step checklist.

---

### Prerequisites Before Capturing Screenshots
1. Ensure your Streamlit app is running:
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```
2. Open your web browser to: `http://localhost:8501`
3. Click the sidebar button: **"📁 Load Sample Test Candidates"**
4. Ensure the Role Preset is set to: **"AI / Machine Learning Engineer"**
5. Click the primary button: **"🚀 Run Screening & Matching Analysis"**

---

### Screenshot Checklist for Report & Presentation

| # | Screenshot Identifier | Section / Tab | What to Frame in the Capture | Purpose in Final Documentation |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `01_app_overview_inputs.png` | Main Screen (Top) | Top title, Ethical AI banner, Job Description text area (AI Engineer preset), and uploaded candidate list in the right column. | Shows the clean input interface, role preset selector, and upload options. Include in Project Report Section 7. |
| **2** | `02_sidebar_controls.png` | Sidebar Controls | Model active badge (`🟢 Model Active: all-MiniLM-L6-v2`), Semantic Similarity Weight slider ($0.60$), and Shortlist Threshold slider ($60\%$). | Demonstrates offline local model badge, privacy guarantee, and recruiter parameter controls. |
| **3** | `03_summary_metrics_cards.png` | Results Overview | The 4 KPI cards: **Total Resumes Analyzed (4)**, **Highest Match Score (79.9%)**, **Average Match Score**, and **Resumes Shortlisted (1)**. | Demonstrates high-level recruiter decision support. Place at the top of Results section. |
| **4** | `04_leaderboard_tab.png` | Tab 1: Leaderboard | The candidate ranking table showing Rank #1 to #4, candidate names, Overall Match %, Semantic Sim %, Skill Match %, and Decision Status. | Core demonstration of candidate ranking, sorting dropdown, and shortlist filter. |
| **5** | `05_candidate_deepdive.png` | Tab 2: Deep Dive (Top) | Candidate header for **Alex Rivera** (Green "SHORTLISTED" badge), Email, Word Count, and the 3 progress bars (Overall, Semantic, Skill). | Demonstrates individual candidate evaluation and visual score gauges. |
| **6** | `06_formula_and_evidence.png` | Tab 2: Deep Dive (Middle) | The blue mathematical formula card (`78.8% * 0.6 + 81.6% * 0.4 = 79.9%`), color-coded skill pills, and the **"Verified Job-Related Evidence"** green quote boxes. | Proves zero hallucination, transparent mathematical scoring, and verifiable evidence extraction. Essential for viva! |
| **7** | `07_score_benchmarking_chart.png` | Tab 3: Comparative Matrix | The **Candidate Score Benchmarking** bar chart comparing Overall Match, Semantic Similarity, and Skill Match across all 4 candidates. | Visual proof of comparative multi-candidate benchmarking. Ideal for Slide 11 of the presentation. |
| **8** | `08_skills_breakdown_chart.png` | Tab 3: Comparative Matrix | The **Technical Skills Breakdown by Candidate** bar chart showing counts of Matched Skills, Missing Skills, and Bonus Skills. | Visualizes quantitative skill gaps across applicants. |
| **9** | `09_xai_feedback_tab.png` | Tab 4: Explainable AI | The XAI feedback screen for Alex Rivera or Priya Sharma showing **Key Strengths**, **Skill & Context Gaps**, and **Actionable Improvement Tips**. | Highlights explainability, candidate guidance, and actionable feedback. |
| **10** | `10_technical_docs_tab.png` | Tab 5: Architecture | System Overview, mathematical formulas ($S_{\text{semantic}}$ cosine formula and $S_{\text{skill}}$ formula), and ethical bias mitigation guidelines. | Demonstrates academic rigor and embedded documentation. |
| **11** | `11_csv_exported_report.png` | External / Excel | Open the downloaded `ai_resume_screening_report.csv` in Microsoft Excel or Notepad, showing clean columns and sanitized formula cells. | Proves CSV export capability, audit trail readiness, and formula injection protection. |
| **12** | `12_terminal_tests_passed.png` | VS Code Terminal | The PowerShell terminal showing `Ran 30 tests in 16.489s OK` and `[SUCCESS] ALL PIPELINE TESTS PASSED!`. | Demonstrates engineering quality and rigorous automated verification. |

---

### Tips for High-Quality Captures
- **Resolution**: Use standard 1080p ($1920 \times 1080$) browser zoom ($100\%$ or $90\%$) for crisp text readability.
- **Tools**: On Windows, press `Windows Key + Shift + S` (Snipping Tool) to capture specific regions, or `Alt + PrtScn` to capture the active window.
- **Naming**: Save files in a `screenshots/` folder using the exact identifiers listed above (e.g., `04_leaderboard_tab.png`).
