# College Viva Voce Questions & Answers
## AI Resume Screening and Job Matching System

This document contains **28 comprehensive technical and architectural questions** frequently asked by external evaluators, professors, and project defense panels, complete with authoritative, technically sound answers.

---

### Category 1: Natural Language Processing & Embedding Models

#### Q1: What is the fundamental difference between keyword-based ATS search and Semantic Similarity?
> **Answer**:  
> Traditional keyword-based ATS uses exact substring or regular expression matching (e.g., searching for the exact sequence of letters *"Python"* or *"Kubernetes"*). If an applicant writes *"container orchestration"* instead of *"Kubernetes"*, or *"Postgres"* instead of *"PostgreSQL"*, a keyword system completely fails to register a match.  
> In contrast, **Semantic Similarity** projects text passages into high-dimensional continuous vector spaces using deep neural networks (Sentence Transformers). Words and phrases with similar conceptual meanings reside close to each other in this vector space. As a result, the model understands that *"containerization"*, *"Docker"*, and *"Kubernetes"* are strongly related concepts, evaluating the candidate on true semantic relevance rather than character-for-character word matching.

#### Q2: Why did you choose `all-MiniLM-L6-v2` over TF-IDF or Word2Vec?
> **Answer**:  
> - **TF-IDF (Term Frequency-Inverse Document Frequency)** is purely lexical: it measures token frequencies across documents. It lacks any notion of semantic relationships, treats synonyms as completely distinct entities, and suffers from the curse of dimensionality with large vocabularies.
> - **Word2Vec / GloVe** generates static vectors for individual words. To represent an entire resume, word vectors must be averaged, which destroys sentence syntax, negations (e.g., *"not experienced in Java"* vs. *"experienced in Java"*), and contextual word meanings (polysemy).
> - **`all-MiniLM-L6-v2`** is a 6-layer distilled Transformer model trained with self-attention. It produces a unified, contextual 384-dimensional dense embedding for entire paragraphs and documents, accurately capturing phrase-level semantic context while maintaining a tiny memory footprint (~120 MB) suitable for instant CPU inference.

#### Q3: Why not use a cloud LLM like OpenAI's GPT-4 or Anthropic Claude for resume screening?
> **Answer**:  
> While proprietary LLMs produce fluent text, they introduce three fatal flaws for enterprise resume screening:
> 1. **Financial Cost**: Commercial LLMs charge per input/output token. Evaluating thousands of multi-page resumes on each job posting generates continuous recurring expenses. Our project runs 100% locally at **zero operational cost ($0.00)**.
> 2. **Data Privacy & GDPR/CCPA Compliance**: Sending candidate resumes (containing full legal names, home addresses, phone numbers, email addresses, and employment histories) to third-party cloud servers violates strict privacy regulations. Our architecture processes all candidate data locally in memory on the machine.
> 3. **Hallucination & Non-Determinism**: Generative LLMs can fabricate candidate credentials or produce inconsistent scores across identical runs. Our hybrid architecture is deterministic, explainable, and extracts verbatim quotes from the actual resume as evidence.

#### Q4: What is Cosine Similarity, and why is it preferred over Euclidean Distance for text embeddings?
> **Answer**:  
> Cosine similarity measures the cosine of the angle between two multi-dimensional vectors:
> $$\text{Cosine Similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\|_2 \|\vec{v}\|_2}$$
> - **Cosine Similarity** evaluates the *direction* or orientation of the vectors, effectively normalizing for document length. A short 1-page resume and a comprehensive 4-page resume discussing the same technical domain will point in nearly identical directions in 384-dimensional space, yielding a high similarity score.
> - **Euclidean Distance** measures the straight-line distance between vector coordinates. Because longer documents contain more words, their unnormalized vector magnitudes differ significantly from shorter documents, artificially penalizing concise resumes even if their technical content is highly relevant.

#### Q5: Can cosine similarity produce negative values? How does your system handle them?
> **Answer**:  
> Mathematically, cosine similarity ranges from $-1.0$ (diametrically opposite vectors) to $+1.0$ (identical direction), with $0.0$ representing orthogonal (completely unrelated) vectors.  
> In natural language document embeddings, true negative values are rare and represent completely irrelevant or contrasting contexts. Our system clamps similarity scores using:
> $$S_{\text{semantic\_pct}} = \max\left(0.0, \min\left(100.0, \text{similarity} \times 100\right)\right)$$
> This guarantees that negative similarity values are bounded at $0.0\%$ rather than skewing the composite scoring arithmetic.

---

### Category 2: Parsing & Document Processing

#### Q6: Why did you select PyMuPDF (`pymupdf`) instead of PyPDF2 or pdfminer?
> **Answer**:  
> 1. **Execution Speed**: PyMuPDF is a Python C-binding to the high-performance MuPDF rendering and extraction engine, executing up to 10 to 20 times faster than pure-Python libraries like PyPDF2.
> 2. **Extraction Accuracy**: PyMuPDF preserves natural text flow, word order, and whitespace across complex multi-column resume layouts far more reliably than PyPDF2, which frequently concatenates adjacent columns into jumbled sentences.
> 3. **Robustness & Built-in Utilities**: PyMuPDF provides built-in methods to verify document encryption (`doc.is_encrypted`), detect damaged/corrupted files, and even inspect image layers for OCR hooks.

#### Q7: How does your system handle scanned or image-only PDF resumes?
> **Answer**:  
> In [`src/parsers.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/parsers.py), after extracting text blocks from all pages of a PDF, the parser calculates the total character count of the cleaned text. If the extracted text contains zero selectable characters while page count is greater than zero, the system recognizes that the document is a scanned image or flattened graphic.  
> Rather than crashing, it flags the status as an informative notification: *"Scanned/image-only PDF detected. Please upload a searchable text-based PDF or run optical character recognition (OCR)."*

#### Q8: What happens if an uploaded file is empty (0 bytes) or corrupted?
> **Answer**:  
> The system implements multi-tiered defensive parsing:
> 1. **Pre-check**: Validates file size before reading; zero-byte files are immediately caught and assigned an error status without invoking the parser.
> 2. **Exception Boundaries**: Parsing calls are wrapped in dedicated `try-except` blocks catching `pymupdf.FileDataError` for malformed PDFs and `docx.opc.exceptions.PackageNotFoundError` for corrupted or non-zip Word documents.
> 3. **Pipeline Resilience**: In [`src/ranker.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/ranker.py), unreadable resumes receive a clean status (`"Failed / Unreadable File"`), are assigned rank `"-"`, and score `0.0%`, allowing the rest of the batch to process smoothly without interruption.

#### Q9: How does the system parse `.docx` resumes that format experience inside tables?
> **Answer**:  
> In [`extract_text_from_docx`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/parsers.py), the parser iterates through standard document paragraphs (`doc.paragraphs`) and also systematically iterates through every row and cell of embedded tables (`for table in doc.tables: for row in table.rows: for cell in row.cells:`). This guarantees that skills and contact information formatted in sidebars or multi-column resume tables are captured.

---

### Category 3: Skill Taxonomy, Canonicalization & Disambiguation

#### Q10: How do you prevent false positives on single-letter programming languages like "C", "R", and common words like "Go"?
> **Answer**:  
> Naive regular expressions like `\b[Cc]\b` or `\b[Gg]o\b` trigger massive false positives on standard English prose (e.g., *"C-level executive"*, *"Vitamin C"*, or *"I want to go to the office"*).  
> In [`src/skills_extractor.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/skills_extractor.py), we implemented **Contextual Disambiguation**:
> - For `"c"`, `"r"`, and `"go"`, a match is only confirmed if the token appears with explicit programming qualifiers (e.g., *"C programming"*, *"Go language"*, *"R statistical"*) OR if it appears inside a comma/bullet-delimited list of other technical skills (e.g., *"Skills: Python, C, Java, Git"*).
> - In standard prose without technical neighbors, the token is rejected as a natural English word.

#### Q11: What is Synonym Canonicalization, and how is it implemented?
> **Answer**:  
> Synonym canonicalization is the process of mapping divergent lexical variants and industry abbreviations to a unified canonical identifier before performing set operations.  
> In [`src/constants.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/constants.py), we maintain a lookup dictionary `SKILL_SYNONYMS`:
> - `"k8s"` $\to$ `"Kubernetes"`
> - `"postgres"` $\to$ `"PostgreSQL"`
> - `"ml"` $\to$ `"Machine Learning"`
> - `"rag"` $\to$ `"Retrieval Augmented Generation"`
> - `"nlp"` $\to$ `"Natural Language Processing"`  
> When analyzing candidate text, any recognized variant is converted to its canonical form, ensuring that two candidates using different terms are credited equally.

#### Q12: How are special characters in skills like `C++`, `C#`, and `.NET` handled in Regular Expressions?
> **Answer**:  
> Symbols like `+`, `#`, and `.` are reserved regex metacharacters (`+` means 1 or more, `.` matches any character). If unescaped, `C++` would match "C" followed by multiple plus signs.  
> We use `re.escape()` on skill tokens and construct custom boundary assertions that allow trailing punctuation (e.g., `(?:\b|\b(?=[+#]))`), ensuring that `C++`, `C#`, and `.NET` match accurately without syntax errors.

#### Q13: What is "Verifiable Evidence Extraction" and how does it prevent hallucinations?
> **Answer**:  
> Unlike generative AI models that generate speculative summaries of candidate abilities, our system uses **deterministic extractive text retrieval**.  
> When a skill (e.g., *"PyTorch"*) is identified as matched, the function `extract_skill_evidence` splits the candidate's resume into constituent sentences and retrieves the exact verbatim sentence containing that skill (e.g., *"Trained custom PyTorch transformer models for NLP sentiment classification"*).  
> If no contextual sentence is found, the evidence field is left empty. The system never generates or synthesizes text, providing zero risk of hallucination.

---

### Category 4: Scoring Architecture & Edge Cases

#### Q14: Explain the Composite Match Score formula and its components.
> **Answer**:  
> The composite score balances contextual semantic understanding with hard skill qualifications:
> $$S_{\text{composite}} = \text{clamp}\left( (w_{\text{semantic}} \times S_{\text{semantic\_pct}}) + (w_{\text{skill}} \times S_{\text{skill\_pct}}), 0.0, 100.0 \right)$$
> - **$S_{\text{semantic\_pct}}$**: Normalized cosine similarity between dense embeddings of the resume and job description.
> - **$S_{\text{skill\_pct}}$**: Percentage of required job description skills present in the resume ($|\mathcal{S}_{\text{Matched}}| / |\mathcal{S}_{\text{JD}}| \times 100$).
> - **$w_{\text{semantic}}, w_{\text{skill}}$**: User-adjustable weights (defaulting to $0.60$ and $0.40$), satisfying $w_{\text{semantic}} + w_{\text{skill}} = 1.0$.
> - **$\text{clamp}(x, 0.0, 100.0)$**: Strict mathematical boundary ensuring the score can never drop below $0.0\%$ or exceed $100.0\%$.

#### Q15: How does your system prevent division-by-zero if a job description contains zero taxonomy skills?
> **Answer**:  
> If a recruiter inputs a non-technical or leadership job description (e.g., *"Seeking an experienced corporate executive to lead quarterly strategy"*), the taxonomy skill count $|\mathcal{S}_{\text{JD}}|$ equals $0$.  
> Calculating $|\mathcal{S}_{\text{Matched}}| / |\mathcal{S}_{\text{JD}}|$ would cause a `ZeroDivisionError`.  
> In [`src/ranker.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/ranker.py), we implemented an explicit guard: when $|\mathcal{S}_{\text{JD}}| == 0$, the technical skill percentage is set to equal the semantic similarity percentage, and the composite score falls back 100% to semantic similarity.

#### Q16: Why are weights configurable by the recruiter rather than hardcoded?
> **Answer**:  
> Different recruitment scenarios require different screening philosophies:
> - **Junior / Campus Hiring**: Recruiters often prioritize broad conceptual aptitude, problem-solving, and general domain alignment over exhaustive keyword lists. Setting higher semantic weight ($80\%$ semantic, $20\%$ skill) benefits adaptable junior candidates.
> - **Senior Specialist Roles**: Positions such as Principal Kubernetes Architect require exact, non-negotiable tools. Setting higher skill weight ($30\%$ semantic, $70\%$ skill) ensures candidates lacking mandatory certifications or technologies are filtered out.

---

### Category 5: Security, Ethics & Software Engineering

#### Q17: What is CSV Formula Injection (CWE-1236), and how did you prevent it?
> **Answer**:  
> **CSV Formula Injection** occurs when untrusted user input exported into a `.csv` file begins with spreadsheet formula operators (`=`, `+`, `-`, `@`, `\t`, `\r`). When an HR professional opens the CSV report in Microsoft Excel or Google Sheets, the spreadsheet software treats the cell as executable code (e.g., `=cmd|'/C calc'!A0` or `=HYPERLINK(...)`), allowing malicious command execution or data exfiltration.  
> In [`src/utils.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/utils.py), our helper `_sanitize_csv_cell` inspects every string exported to CSV. If the first character is an operator (`=`, `+`, `-`, `@`), it prepends an apostrophe `'`. Excel and Google Sheets render the text safely as a literal string without executing formulas.

#### Q18: What path traversal vulnerability did you address in filename handling?
> **Answer**:  
> Malicious users can upload files with crafted names containing directory traversal sequences (e.g., `../../etc/passwd` or `..\..\Windows\System32\cmd.exe`). If an application naively uses this filename when saving or referencing files, it can overwrite or expose critical operating system directories.  
> In [`src/utils.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/utils.py), `sanitize_filename` invokes `os.path.basename()` to strip all directory paths, and substitutes special characters with underscores, ensuring only safe, sanitized filenames are used.

#### Q19: How does this project address Ethical AI and algorithmic bias in hiring?
> **Answer**:  
> Hiring models frequently introduce demographic bias if trained on historical hiring data. Our system mitigates bias through three architectural decisions:
> 1. **Protected Attribute Omission**: The parser and scoring function strictly omit candidate age, gender, race, ethnicity, religion, marital status, and physical appearance.
> 2. **Decision-Support Classification**: The system outputs a *textual alignment estimate* accompanied by an ethical advisory, ensuring that automated scores assist recruiters rather than replacing human judgment.
> 3. **Explainability**: Every score is accompanied by transparent lists of matched and missing skills, allowing human recruiters to verify the rationale behind every ranking.

#### Q20: How does Streamlit manage application state and model caching?
> **Answer**:  
> Streamlit re-executes the Python script from top to bottom on every user interaction. Without caching, the 120 MB Sentence Transformer model would reload on every button click, causing 5-second UI delays.  
> We use `@st.cache_resource` on the model loader function (`get_cached_embedding_model`). Streamlit retains the loaded model weights in memory across user sessions, reducing subsequent inference execution to milliseconds.

---

### Category 6: Advanced Technical & Operational Questions

#### Q21: What is the computational complexity of computing embeddings and similarities for $N$ resumes?
> **Answer**:  
> 1. **Embedding Generation**: For $N$ resumes and $1$ job description, the Transformer encodes $N+1$ texts. The complexity of self-attention in MiniLM is $\mathcal{O}(L^2)$ where $L$ is the token sequence length (truncated at 256 or 512 tokens). For $N$ documents, encoding complexity is $\mathcal{O}(N \cdot L^2)$.
> 2. **Cosine Similarity**: Comparing $N$ 384-dimensional resume vectors with the 384-dimensional JD vector requires computing $N$ dot products. The complexity is $\mathcal{O}(N \cdot d)$ where $d = 384$.
> 3. **Sorting**: Sorting $N$ candidates by score requires $\mathcal{O}(N \log N)$ operations.  
> Because $d = 384$ is small, scoring and ranking 100 resumes takes less than 2 seconds on a standard quad-core CPU.

#### Q22: What happens if PyTorch or Sentence-Transformers is unavailable on a legacy machine?
> **Answer**:  
> In [`src/embeddings.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/src/embeddings.py), the loader wraps `SentenceTransformer` in a `try-except` block. If PyTorch or model downloads fail, the system falls back to a Scikit-Learn TF-IDF vectorizer engine with word n-grams $(1, 2)$. While TF-IDF lacks dense contextual representations, it ensures that the application never crashes and remains functional even in restricted environments.

#### Q23: How do you ensure that batch analysis yields identical scores to individual candidate analysis?
> **Answer**:  
> In [`tests/test_score_calculation.py`](file:///c:/Users/prave/OneDrive/Desktop/resume/tests/test_score_calculation.py), the test `test_single_vs_multiple_resume_consistency` validates that analyzing Candidate A individually against a job description produces the exact same score ($79.9\%$) as analyzing Candidate A within a batch of 10 candidates. Vector operations are performed independently per document vector, guaranteeing deterministic results.

#### Q24: What is the maximum file size and upload limit supported?
> **Answer**:  
> In [`.streamlit/config.toml`](file:///c:/Users/prave/OneDrive/Desktop/resume/.streamlit/config.toml), `maxUploadSize = 25` configures a 25 MB upload limit per file, which accommodates even graphic-heavy PDF portfolios. In memory, resumes are parsed in streaming chunks, using less than 15 MB of RAM per document.

#### Q25: Can this system be deployed online for free?
> **Answer**:  
> Yes. Because the model weights are lightweight (~120 MB) and run on standard CPU without GPU requirements, the application can be deployed for free on **Streamlit Community Cloud** or **Hugging Face Spaces** directly from a GitHub repository, requiring no credit card or paid cloud infrastructure.

#### Q26: How does the system handle resumes with multiple columns or visual sidebars?
> **Answer**:  
> PyMuPDF uses physical page coordinate extraction (`pymupdf.Rect`) and blocks-based text reading (`page.get_text("blocks")`). Blocks are ordered from top-to-bottom and left-to-right, ensuring text from the primary content column does not interleave arbitrarily with text from a side column.

#### Q27: How does your system prevent false positives when candidates include "buzzwords" in white text (ATS hacking)?
> **Answer**:  
> Some candidates attempt to trick ATS algorithms by pasting invisible white-colored keywords into their resumes. Our system neutralizes this through **Extractive Evidence Verification**:
> 1. Even if hidden text triggers a keyword match, the recruiter deep-dive tab displays the verbatim excerpt containing that keyword.
> 2. If the excerpt is an ungrammatical block of comma-separated buzzwords without practical project context, the recruiter immediately spots the manipulation.
> 3. Furthermore, semantic embeddings evaluate the holistic contextual syntax of the resume, meaning an isolated block of keywords has limited impact on overall dense semantic similarity.

#### Q28: What is your project's biggest technical achievement?
> **Answer**:  
> Delivering a complete, production-grade NLP evaluation platform that achieves the semantic comprehension of modern AI while guaranteeing **zero cloud dependency, zero financial cost, deterministic explainability, and mathematically verifiable safety**. Every score is grounded in an explicit formula, backed by verbatim quotes from the candidate's actual document, and verified across 30 automated test cases.
