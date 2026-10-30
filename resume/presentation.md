# Presentation Deck: AI Resume Screening and Job Matching System
## 10–12 Slide PowerPoint Presentation Outline for College Project Defense

---

### Slide 1: Title Slide
- **Title:** AI Resume Screening and Job Matching System
- **Subtitle:** Intelligent Decision Support using Pretrained Sentence Transformers & Skill Taxonomy Matching
- **Project Type:** College Mini Project / Capstone Project
- **Presenter:** [Your Name / Team Members]
- **Department:** Department of Computer Science & Engineering
- **Mentor / Guide:** [Internal Guide / Professor Name]
- **Academic Year:** 2025–2026
- **Visual Suggestion:** Minimalist title layout with project logo, Python and Streamlit icons, and a clean professional color theme (Deep Navy `#1E3A8A` and Cobalt Blue `#2563EB`).
- **Speaker Notes:**  
  *"Good morning respected evaluators and panel members. Today, we are presenting our project: 'AI Resume Screening and Job Matching System'. This system addresses the inefficiencies of traditional keyword ATS systems by combining modern dense semantic transformer embeddings with transparent, explainable skill taxonomy matching—running 100% locally on standard hardware without any external API costs."*

---

### Slide 2: Problem Statement & Motivation
- **The Recruitment Bottleneck:**
  - HR teams receive 250+ resumes per job opening; average initial review takes only 6 to 8 seconds.
- **Flaws in Existing ATS Systems:**
  - **Keyword Rigidity:** Fails when candidates use synonyms (e.g., *"cloud orchestration"* vs. *"Kubernetes"*).
  - **The Lexical Chasm:** Superficial keyword matching rewards candidates who "stuff" keywords rather than demonstrating relevant domain experience.
  - **Black-Box Cloud LLMs:** Sending candidate resumes to proprietary cloud APIs (such as OpenAI) introduces recurring token costs, API rate limits, and serious data privacy/GDPR compliance risks.
- **Our Motivation:**  
  Build an offline, privacy-preserving, zero-cost, and explainable AI system that assists recruiters fairly and accurately.
- **Speaker Notes:**  
  *"Traditional ATS software often misses qualified applicants simply because they phrased their experience differently. Meanwhile, using commercial cloud APIs costs money and sends private applicant resumes to third-party servers. Our goal was to create a local, intelligent system that understands meaning, extracts verified proof, and costs nothing to operate."*

---

### Slide 3: Objectives & Proposed Solution
- **Core Project Objectives:**
  1. Ingest and normalize multi-format resumes (`.pdf` and `.docx`) with error boundary protection.
  2. Implement deep semantic text embeddings via a pretrained Sentence Transformer model (`all-MiniLM-L6-v2`).
  3. Extract technical skills using a categorized taxonomy with synonym canonicalization (`k8s` $\to$ `kubernetes`).
  4. Formulate a transparent, bounded composite scoring mechanism combining contextual semantics and hard skills.
  5. Provide Explainable AI (XAI) diagnostics: matched skills, missing prerequisites, and verbatim resume evidence snippets.
  6. Deliver an interactive Streamlit dashboard with leaderboards, comparative charts, and injection-safe CSV exports.
- **Key Proposition:** High-accuracy semantic screening running 100% locally on CPU with zero data leakage.
- **Speaker Notes:**  
  *"Our proposed solution bridges the gap between deep contextual understanding and exact rule-based verification. It gives recruiters a transparent formula rather than a mysterious black-box number, complete with direct quotes from the resume verifying each claimed skill."*

---

### Slide 4: System Architecture & Workflow
- **End-to-End Pipeline:**
  1. **Document Ingestion Layer:** PyMuPDF (PDF) & python-docx (DOCX) $\to$ text sanitization & bullet normalization.
  2. **Dual-Track AI Analysis:**
     - **Track A (Semantic Context):** Dense 384-dimensional vector embeddings via `all-MiniLM-L6-v2` $\to$ Cosine Similarity.
     - **Track B (Technical Taxonomy):** Regex tokenization + Synonym Canonicalization $\to$ Matched / Missing / Bonus skills.
  3. **Scoring & Decision Support:** Dynamic weighted composite score ($w_{\text{sem}} \times S_{\text{sem}} + w_{\text{skill}} \times S_{\text{skill}}$) $\to$ Shortlist classification.
  4. **Reporting Layer:** Interactive Streamlit Dashboard $\to$ Sanitized CSV export.
- **Visual Suggestion:** Insert the clean Mermaid workflow flowchart from the project report.
- **Speaker Notes:**  
  *"Here is our system architecture. Notice the dual-track design: Track A computes contextual dense embeddings using Sentence Transformers, while Track B performs deterministic skill extraction with synonym resolution. Both streams merge into a transparent scoring engine that outputs verifiable results."*

---

### Slide 5: NLP Engine — Sentence Transformers & Cosine Similarity
- **Why Sentence Transformers (`all-MiniLM-L6-v2`)?**
  - Distilled 6-layer MiniLM architecture; only ~120 MB memory footprint.
  - Maps sentences and documents to a shared 384-dimensional continuous vector space.
  - Captures complex semantic relationships, synonyms, and context without character-matching constraints.
- **Mathematical Cosine Similarity:**
  $$\text{Cosine Similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\|_2 \|\vec{v}\|_2}$$
  - Measures the cosine of the angle between resume vector $\vec{u}$ and job description vector $\vec{v}$.
  - Identical semantic orientation yields $1.0$ ($100\%$); irrelevant content yields values near $0.0$.
- **Offline CPU Execution:**
  - Model weights load in $<1$ second once cached. Zero cloud dependency.
- **Speaker Notes:**  
  *"Instead of treating words as isolated tokens like TF-IDF or Word2Vec, `all-MiniLM-L6-v2` uses self-attention to generate holistic 384-dimensional representations. We calculate the cosine similarity between the resume vector and the job description vector to gauge conceptual alignment."*

---

### Slide 6: Skill Taxonomy, Synonyms & False-Positive Disambiguation
- **Comprehensive Domain Taxonomy:**
  - 6 Core Categories: Programming, Web Development, AI/Machine Learning, Cloud & DevOps, Databases, and Soft Skills.
- **Synonym Canonicalization (`SKILL_SYNONYMS`):**
  - Variations are automatically unified:
    - `k8s` $\to$ `kubernetes`
    - `postgres` $\to$ `postgresql`
    - `ml` $\to$ `machine learning`
    - `rag` $\to$ `retrieval augmented generation`
- **Contextual Disambiguation Engine:**
  - Prevents false-positive matches on single letters and common English words (`C`, `R`, `Go`).
  - Matches only if surrounded by programming context (e.g., *"C programming"*, *"Go language"* or within technical skill lists).
- **Speaker Notes:**  
  *"One of our biggest technical achievements is resolving false positives. A typical keyword scanner matching 'C' or 'Go' triggers on common English sentences like 'I can go to the office'. Our disambiguation engine verifies true technical context before registering a match."*

---

### Slide 7: Transparent Composite Scoring & Verifiable Evidence
- **Mathematical Formula:**
  $$\text{Final Score} = \text{clamp}\left( (w_{\text{semantic}} \times S_{\text{semantic}}) + (w_{\text{skill}} \times S_{\text{skill}}), 0.0, 100.0 \right)$$
- **Configurable Weights:**
  - Default: $60\%$ Semantic Similarity $+ 40\%$ Technical Skill Overlap.
  - Fully adjustable via sidebar sliders for different hiring stages.
- **Zero-Division Edge Case Protection:**
  - If a job description contains zero taxonomy skills, the system gracefully falls back $100\%$ to semantic similarity without crashing.
- **Verifiable Evidence Extraction (Zero Hallucination):**
  - Extracts the exact verbatim sentence from the resume demonstrating the matched skill.
  - Never invents or generates hypothetical candidate achievements.
- **Speaker Notes:**  
  *"Recruiters don't trust unexplained black-box scores. Our system shows the exact mathematical formula for every candidate. Furthermore, we extract the verbatim sentence from the resume where each skill was found, ensuring 100% verifiable evidence without hallucination."*

---

### Slide 8: Safety, Robustness & Privacy by Design
- **Robust Multi-Format Parsing:**
  - Handles valid, empty (0-byte), corrupted, and password-encrypted PDF and DOCX files.
  - Automatically identifies scanned/image-only PDFs and provides informative notices.
- **CSV Formula Injection Protection (CWE-1236):**
  - Cells starting with dangerous spreadsheet operators (`=`, `+`, `-`, `@`) are safely prepended with `'` to neutralize macro execution in Microsoft Excel.
- **Path Traversal Sanitization:**
  - Strips hazardous filename paths (`../../etc/passwd`) using `os.path.basename`.
- **Ethical AI & Bias Mitigation:**
  - Scoring strictly excludes protected personal characteristics (gender, age, ethnicity, religious indicators).
  - Explicitly labeled as a *decision-support textual alignment estimate*, preserving human recruiter agency.
- **Speaker Notes:**  
  *"We treated safety and security as top priorities. We implemented protection against CSV formula injection attacks, sanitized filenames, and built error handlers for corrupt and encrypted files. Most importantly, we exclude personal demographic data to ensure bias-free, merit-based screening."*

---

### Slide 9: Live Demonstration & Dashboard Features
- **Key Dashboard Highlights:**
  - **4 Top-Level Metric KPI Cards:** Total Resumes, Highest Score, Average Score, Shortlist Count.
  - **Tab 1 — Candidate Leaderboard:** Interactive sorting (by overall match, semantic score, skill match, or candidate name) and shortlist filter.
  - **Tab 2 — Candidate Deep Dive:** Visual progress gauges, mathematical formula card, color-coded skill pills (green=matched, red=missing, blue=bonus), and verbatim evidence excerpts.
  - **Tab 3 — Comparative Matrix:** Dual comparative bar charts (Score Benchmarking & Technical Skills Count Breakdown) plus cross-candidate summary tables.
  - **Tab 4 — Explainable AI (XAI) Feedback:** Detailed candidate strengths, gaps, and concrete suggestions for resume enhancement.
  - **Tab 5 — Technical Architecture & Ethics:** Full theoretical background, formulas, and viva guide.
- **Speaker Notes:**  
  *"Now let us look at the Streamlit user interface. The UI features four primary KPI cards, dynamic sorting controls, interactive charts, and deep-dive candidate profiles with color-coded skill badges."*

---

### Slide 10: Testing Methodology & Real Verification Results
- **Automated Test Suite (30 Tests Passed):**
  - **10 Unit Tests:** Text normalization, metadata regex, PDF/DOCX parsers, empty/corrupted document handling.
  - **5 Taxonomy Tests:** C++, C#, .NET symbols, multi-word matching, single-letter disambiguation.
  - **5 Embedding & Ranking Tests:** Model loading, semantic separation, batch similarity consistency.
  - **3 CSV & Security Tests:** Formula injection sanitization, filename neutralization, column validation.
  - **7 Score Calculation Tests:** Varying weights, score bounds $[0, 100]$, zero-skill JD fallback, synonym unification.
- **Execution Time:** 30 unit tests completed in **$16.489$ seconds** with $100\%$ pass rate (`OK`).
- **Speaker Notes:**  
  *"We verified our implementation with 30 comprehensive automated tests spanning parsing, embedding, score bounds, synonym unification, and security. All 30 tests pass cleanly in under 17 seconds."*

---

### Slide 11: Real Benchmark Results
- **Sample Screening Scenario (Role: AI / Machine Learning Engineer):**

| Rank | Candidate Profile | Format | Overall Match | Semantic Sim | Skill Match | Decision Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Alex Rivera** (AI Engineer) | PDF | **$79.9\%$** | $78.8\%$ | $81.6\%$ | 🟢 **Shortlisted** |
| **#2** | **Priya Sharma** (Full-Stack Dev) | DOCX | **$43.3\%$** | $47.7\%$ | $36.8\%$ | 🟡 **Under Review** |
| **#3** | **Jordan Lee** (Data Scientist) | PDF | **$39.2\%$** | $49.6\%$ | $23.7\%$ | 🟡 **Under Review** |
| **#4** | **Sam Taylor** (Junior Dev) | PDF | **$31.5\%$** | $47.2\%$ | $7.9\%$ | 🟡 **Under Review** |

- **Key Takeaways:**
  - Domain-relevant candidates are accurately separated from unrelated applicants.
  - Semantic similarity appropriately rewards relevant technical experience even without exact keyword overlap.
- **Speaker Notes:**  
  *"Here are the real screening results for an AI Engineer position. Alex Rivera, who has strong PyTorch, Docker, and AWS experience, achieved a 79.9% match and was shortlisted. Priya Sharma and Jordan Lee scored in the 40% range due to partial overlap, while the junior profile scored 31.5%. The ranking is logical, stable, and completely explainable."*

---

### Slide 12: Conclusion & Future Scope
- **Project Summary:**
  - Developed a complete, fully functional AI resume screening and job matching platform.
  - Achieved deep semantic understanding with zero paid API costs and 100% data privacy.
  - Delivered verifiable evidence extraction, complete transparency, and robust security.
- **Future Enhancements:**
  - Integrate native Tesseract OCR for scanned PDF image extraction.
  - Implement blind screening mode (automated PII redaction of names and emails).
  - Add multilingual sentence transformers for cross-lingual resume matching.
- **Q&A:**
  - Thank you! We welcome questions from the examination board.
- **Speaker Notes:**  
  *"In conclusion, our project demonstrates that efficient, ethical, and explainable AI can be delivered using lightweight local open-source models without relying on expensive, black-box cloud APIs. Thank you for your time. We are now ready for your questions."*
