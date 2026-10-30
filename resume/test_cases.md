# Comprehensive Test Cases & Verification Matrix
## AI Resume Screening and Job Matching System

This document outlines the complete test matrix for the project, spanning **Normal Operation**, **Boundary / Edge Cases**, and **Error Handling / Security Scenarios**. All test cases have been executed against the running Python test suite (`tests/`) and verified.

---

### Test Execution Summary
- **Total Test Cases Executed:** 30 Automated Unit & Integration Tests
- **Test Results:** 30 Passed, 0 Failed, 0 Errors (`Ran 30 tests in 16.489s OK`)
- **Test Framework:** Python `unittest` standard library
- **End-to-End Pipeline Script:** [`test_pipeline.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/test_pipeline.py) Passed (`[SUCCESS] ALL PIPELINE TESTS PASSED!`)

---

## 1. Normal Test Cases (Standard Functional Operations)

| Test ID | Test Scenario | Inputs / Preconditions | Expected Output | Actual Observed Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC-NORM-01** | Standard PDF Resume Parsing | Valid PDF resume with candidate name, email, phone, and technical experience (`valid.pdf`). | Text cleanly extracted, contact metadata parsed, status marked `"success"`. | Status: `"success"`, word count > 0, email and phone correctly identified. | ✅ **PASS** |
| **TC-NORM-02** | Standard DOCX Resume Parsing | Valid Word `.docx` file containing formatted paragraphs and embedded skill tables. | Complete text extracted across both paragraphs and table cells, status marked `"success"`. | Status: `"success"`, all paragraph and table tokens extracted accurately. | ✅ **PASS** |
| **TC-NORM-03** | Model Initialization | Load pretrained Sentence Transformer (`all-MiniLM-L6-v2`). | Model loads in memory, outputting 384-dimensional embeddings; backend marked `"sentence-transformers"`. | Model weights loaded from local hub cache in <1s; backend verified as `"sentence-transformers"`. | ✅ **PASS** |
| **TC-NORM-04** | Semantic Similarity Differentiation | Compare an AI/ML Engineer resume and an irrelevant Receptionist resume against an AI Job Description. | The AI Engineer resume achieves substantially higher semantic similarity than the irrelevant resume. | AI Resume similarity: ~78.8%; Irrelevant resume similarity: <30.0%. Clear semantic separation. | ✅ **PASS** |
| **TC-NORM-05** | Multi-Word Skill Extraction | Resume text containing multi-token technical skills: *"Machine Learning"*, *"Deep Learning"*, *"Computer Vision"*. | All multi-word skills recognized as singular taxonomy entities. | Extracted: `["Machine Learning", "Deep Learning", "Computer Vision"]`. | ✅ **PASS** |
| **TC-NORM-06** | Special Symbol Skill Recognition | Resume text containing programming languages with punctuation: `C++`, `C#`, `.NET`. | Symbols extracted without regex syntax errors or truncation. | Extracted: `["C++", "C#", ".NET"]` with boundary assertions verified. | ✅ **PASS** |
| **TC-NORM-07** | Skill Gap Categorization | Resume matching 3 JD skills (Python, PyTorch, Docker) and missing 2 (Kubernetes, AWS). | Categorized into Matched (3), Missing (2), and Bonus (1); Match percentage = $60.0\%$. | Matched: `["Python", "PyTorch", "Docker"]`; Missing: `["Kubernetes", "AWS"]`; Skill Match: $60.0\%$. | ✅ **PASS** |
| **TC-NORM-08** | Multi-Candidate Batch Ranking | Batch of 4 resumes with varying relevance to an AI Engineer position. | Candidates sorted in descending order of composite score with ranks 1, 2, 3, 4. | Rank #1 Alex Rivera ($79.9\%$), Rank #2 Priya Sharma ($43.3\%$), Rank #3 Jordan Lee ($39.2\%$), Rank #4 Sam Taylor ($31.5\%$). | ✅ **PASS** |
| **TC-NORM-09** | Shortlist Threshold Classification | Candidates scored with a shortlist threshold configured at $50.0\%$. | Candidate with score $\ge 50.0\%$ flagged as `Shortlisted`; candidates $< 50.0\%$ flagged as `Under Review`. | Candidate Alex Rivera ($79.9\%$) flagged `is_shortlisted: True`; candidates $<50\%$ flagged `is_shortlisted: False`. | ✅ **PASS** |
| **TC-NORM-10** | Explainable AI Feedback | Candidate with $72.0\%$ score, missing Kubernetes and AWS. | Generates qualitative fit tier, bulleted strengths, gap warnings, and actionable optimization tips. | Detailed feedback generated with strengths, missing skill warnings, and quantifiable metrics guidance. | ✅ **PASS** |

---

## 2. Boundary & Edge-Case Test Cases

| Test ID | Test Scenario | Inputs / Preconditions | Expected Output | Actual Observed Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC-EDGE-01** | Zero Taxonomy Skills in Job Description | Job description contains only general management text with 0 technical taxonomy skills. | Prevents division-by-zero (`ZeroDivisionError`); composite score falls back 100% to semantic similarity. | Division by zero avoided; candidate score equals semantic similarity percentage ($78.8\%$). | ✅ **PASS** |
| **TC-EDGE-02** | Extreme Scoring Weights ($1.0, 0.0$) | Configure Semantic Weight = $1.00$, Skill Weight = $0.00$. | Final composite score is determined purely by semantic similarity. | Candidate composite score exactly matches semantic similarity percentage ($78.8\%$). | ✅ **PASS** |
| **TC-EDGE-03** | Extreme Scoring Weights ($0.0, 1.0$) | Configure Semantic Weight = $0.00$, Skill Weight = $1.00$. | Final composite score is determined purely by technical skill match. | Candidate composite score exactly matches technical skill percentage ($81.6\%$). | ✅ **PASS** |
| **TC-EDGE-04** | Score Bounds & Clamping | Perfect match resume (identical text to JD) and empty/unreadable resume. | All composite scores are strictly clamped inside $[0.0, 100.0]$. | Scores verified: Perfect match clamped at $100.0\%$, failed document clamped at $0.0\%$. | ✅ **PASS** |
| **TC-EDGE-05** | Single vs Batch Scoring Consistency | Evaluate Candidate A individually, then evaluate Candidate A within a batch of 10 candidates. | Individual composite score is identical to batch composite score. | `score_single == score_batch == 79.9%`. Zero batch divergence observed. | ✅ **PASS** |
| **TC-EDGE-06** | Synonym Harmonization (`k8s` vs `Kubernetes`) | JD specifies *"Kubernetes, PostgreSQL"*; resume specifies *"k8s, Postgres"*. | Canonicalization maps synonyms to identical keys; skill match percentage evaluates to $100.0\%$. | `k8s` and `Postgres` mapped to `Kubernetes` and `PostgreSQL`; Skill Match evaluates to $100.0\%$. | ✅ **PASS** |
| **TC-EDGE-07** | False Positive Single-Letter Disambiguation | Resume contains standard English prose: *"I am a C-level executive and can go to the office"*. | Words "C" and "go" are rejected as non-programming terms; 0 programming skills extracted. | Extracted skills: `[]`. False positives completely eliminated. | ✅ **PASS** |
| **TC-EDGE-08** | Legitimate Single-Letter Programming Match | Resume contains: *"Technical Skills: Python, C, Java, Go, R"*. | "C", "Go", and "R" recognized as programming languages due to technical list context. | Extracted skills: `["Python", "C", "Java", "Go", "R"]`. | ✅ **PASS** |
| **TC-EDGE-09** | Text Cleaning with Irregular Bullets | Text contains mixed Windows line breaks (`\r\n`), tabs, and Unicode bullet variants (`•`, `▪`, `-`). | Cleaned into uniform standard hyphen bullets (`-`) with normalized single spaces. | Cleaned text contains normalized `- ` bullets without non-printable artifacts. | ✅ **PASS** |
| **TC-EDGE-10** | Verifiable Evidence Retrieval | Resume contains: *"Architected enterprise RAG system using LangChain, Hugging Face, and PyTorch."* | Extracts exact verbatim sentence for `"PyTorch"` without modifying or hallucinating text. | Returns exact sentence containing `"PyTorch"` and `"LangChain"`. | ✅ **PASS** |

---

## 3. Error Handling & Security Test Cases

| Test ID | Test Scenario | Inputs / Preconditions | Expected Output | Actual Observed Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC-ERR-01** | Empty (0-byte) PDF File | Upload a 0-byte file named `empty.pdf`. | Parser catches 0-byte file, returns status `"error"`, prevents downstream model crashes. | Returns: `status="error"`, `error_message="Empty file (0 bytes)."`. App remains stable. | ✅ **PASS** |
| **TC-ERR-02** | Corrupted DOCX File | Upload a binary file with `.docx` extension containing invalid non-ZIP headers. | Caught by `PackageNotFoundError`, returns status `"error"` with helpful message. | Returns: `status="error"`, `error_message="Invalid or corrupted DOCX file."`. | ✅ **PASS** |
| **TC-ERR-03** | Password-Protected / Encrypted PDF | Upload a PDF file with owner/user encryption enabled. | Parser checks `doc.is_encrypted`, aborts extraction gracefully, advises user to decrypt. | Returns: `status="error"`, `error_message="PDF is password-encrypted."`. | ✅ **PASS** |
| **TC-ERR-04** | Scanned / Image-Only PDF | Upload a PDF containing a scanned image of a resume with 0 selectable text characters. | Parser detects page count > 0 with 0 text characters, flags OCR requirement. | Returns: `status="error"`, `error_message="Scanned/image-only PDF detected... OCR required."`. | ✅ **PASS** |
| **TC-ERR-05** | Unsupported File Extension | Upload file named `candidate_resume.exe` or `profile.png`. | Validator rejects upload, specifying only `.pdf` and `.docx` are accepted. | Validation fails: returns error message identifying unsupported extension. | ✅ **PASS** |
| **TC-ERR-06** | Brief Job Description Input | Recruiter submits a job description containing fewer than 20 words. | Validator rejects input, prompting for at least 20 words for meaningful semantic evaluation. | Validation fails: returns warning identifying description is too brief. | ✅ **PASS** |
| **TC-ERR-07** | Empty Job Description Input | Recruiter clicks analyze with a blank job description. | Validator rejects input, prompting user to enter or select a job description. | Validation fails: returns `"Job description cannot be empty."`. | ✅ **PASS** |
| **TC-ERR-08** | CSV Formula Injection (CWE-1236) | Candidate name or skill begins with formula operators (`=1+2`, `@macro`, `+admin`, `-calc`). | Cell value prepended with apostrophe `'` to prevent command execution in Microsoft Excel. | Exported cells verified as `'=1+2`, `'@macro`, `'+admin`. Macro execution neutralized. | ✅ **PASS** |
| **TC-ERR-09** | Path Traversal Filename Sanitization | File uploaded with malicious path traversal string: `../../etc/passwd`. | Filename sanitized using `os.path.basename` and special character replacement. | Sanitized to `"passwd"`. Directory traversal neutralized. | ✅ **PASS** |
| **TC-ERR-10** | Batch Analysis with Failed Files | Batch containing 2 valid resumes and 1 corrupted file. | Valid files are scored and ranked; corrupt file is assigned `Rank -` and score `0.0%` without stopping batch. | Valid files ranked #1 and #2; corrupt file assigned `Rank -`, score `0.0%`, status `"Failed / Unreadable File"`. | ✅ **PASS** |

---

## 4. How to Reproduce All Tests Locally

### Run the Entire Test Suite (30 Tests)
```powershell
.\.venv\Scripts\python.exe -m unittest discover tests -v
```

### Run Dedicated Score Calculation Tests
```powershell
.\.venv\Scripts\python.exe -m unittest tests/test_score_calculation.py -v
```

### Run Dedicated Parser & Safety Tests
```powershell
.\.venv\Scripts\python.exe -m unittest tests/test_resume_system.py -v
```

### Run End-to-End Pipeline Verification
```powershell
.\.venv\Scripts\python.exe test_pipeline.py
```
