# Step-by-Step Online Deployment Guide
## AI Resume Screening and Job Matching System

Deploy your college mini project online so external examiners, professors, and recruiters can test it live from any device (phone, laptop, tablet) via a public HTTPS link.

---

## 🌟 Recommended Deployment Methods (Both 100% Free)

| Platform | Best For | Cost | Hosting Specs | Setup Time |
| :--- | :--- | :---: | :--- | :---: |
| **Streamlit Community Cloud** *(Recommended)* | Official native Streamlit host | **$0.00** | 1 GB RAM, continuous deployment from GitHub | **3 Minutes** |
| **Hugging Face Spaces** | Alternative ML-focused host | **$0.00** | 2 vCPU, 16 GB RAM (Generous free tier) | **4 Minutes** |

---

## Method 1: Deploy to Streamlit Community Cloud (Recommended)

Streamlit Community Cloud is the easiest, most reliable way to host this application. Every time you push code updates to GitHub, your live web app updates automatically.

### Step 1: Upload Your Code to GitHub

#### Option A: Using GitHub Web (No CLI Git Required)
1. Go to [https://github.com](https://github.com) and log in (or create a free account).
2. In the top-right corner, click the **`+`** icon $\to$ select **New repository**.
3. Name your repository (e.g., `ai-resume-screening`).
4. Set visibility to **Public** (required for free Streamlit Cloud hosting).
5. Leave "Add a README file" **unchecked** (we already have a complete README in the project).
6. Click **Create repository**.
7. On the repository page, click the link: **"uploading an existing file"**.
8. Drag and drop all files and folders from your `resume` project folder:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `project_report.md`
   - `presentation.md`
   - `viva_questions.md`
   - `test_cases.md`
   - `test_pipeline.py`
   - Folder: `src/` (contains all Python modules)
   - Folder: `.streamlit/` (contains `config.toml`)
   - Folder: `tests/`
   - Folder: `sample_data/`
   *(Note: Do **NOT** upload the `.venv` folder; your `.gitignore` already excludes it)*
9. Enter commit message: `"Initial commit for AI Resume Screening System"` and click **Commit changes**.

#### Option B: Using VS Code Built-in Git or Git CLI
If you have Git installed:
```powershell
git init
git add .
git commit -m "Initial commit for AI Resume Screening System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-resume-screening.git
git push -u origin main
```

---

### Step 2: Deploy on Streamlit Community Cloud
1. Open [https://share.streamlit.io](https://share.streamlit.io) in your browser.
2. Click **"Sign in with GitHub"** and authorize Streamlit.
3. Once logged in, click the blue button: **"New app"** (or **"Create app"**).
4. Fill in the deployment details:
   - **Repository:** `YOUR_USERNAME/ai-resume-screening`
   - **Branch:** `main` (or `master`)
   - **Main file path:** `app.py`
   - **App URL (optional):** Choose a custom subdomain (e.g., `ai-resume-screening-demo.streamlit.app`)
5. Click **"Deploy!"**.

Streamlit Cloud will automatically:
- Read `requirements.txt` and install all dependencies (`sentence-transformers`, `torch`, `pymupdf`, etc.).
- Apply your custom theme and settings from `.streamlit/config.toml`.
- Download and cache the lightweight `all-MiniLM-L6-v2` model.
- Launch your interactive dashboard at your public URL!

---

## Method 2: Deploy to Hugging Face Spaces (Alternative Free Host)

Hugging Face Spaces provides a free 16 GB RAM environment, which is ideal for machine learning projects.

### Step 1: Create a Space
1. Go to [https://huggingface.co](https://huggingface.co) and sign in.
2. In the top-right profile menu, click **New Space**.
3. Fill in the details:
   - **Space name:** `ai-resume-screening`
   - **License:** `mit` or `open-source`
   - **Space SDK:** Select **Streamlit**
   - **Space hardware:** **CPU basic • 2 vCPU • 16 GB RAM • Free**
4. Click **Create Space**.

### Step 2: Upload Files
1. On your new Space page, click the **Files** tab $\to$ click **Add file** $\to$ **Upload files**.
2. Drag and drop your project files (`app.py`, `requirements.txt`, `src/`, `sample_data/`, etc.).
3. Click **Commit changes to main**.
4. Hugging Face Spaces will build the container and deploy your live app in ~2 minutes!

---

## Method 3: Live Local Network Sharing (For Classroom / Lab Demo)

If you need to demonstrate the app in your college laboratory or classroom without deploying online, you can share the running app across the local college Wi-Fi or LAN:

1. Connect both your laptop and the examiner's device (phone/tablet/laptop) to the same Wi-Fi network.
2. Find your laptop's local IPv4 address:
   ```powershell
   ipconfig
   ```
   *(Look for `IPv4 Address`, e.g., `192.168.1.84`)*
3. Run Streamlit bound to all interfaces:
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
   ```
4. The examiner can open their browser and navigate directly to:
   ```text
   http://192.168.1.84:8501
   ```
   *(Replace with your actual laptop IP address)*

---

## 🔒 Verification & Security Checklist for Deployment

- [x] **No Hardcoded API Keys**: The project uses local `all-MiniLM-L6-v2` inference. Zero secret keys or tokens are stored in the code.
- [x] **Virtual Environment Excluded**: `.venv/` is excluded in `.gitignore` so unnecessary multi-gigabyte local libraries are not pushed to GitHub.
- [x] **Lightweight Memory Usage**: The model uses ~120 MB RAM, well within Streamlit Cloud's 1 GB free allocation and Hugging Face's 16 GB limit.
- [x] **CSV Injection Guard Active**: All downloaded CSV reports sanitize formula characters (`=`, `+`, `-`, `@`), ensuring examiner safety.
- [x] **Sample Candidates Included**: The `sample_data/` folder includes realistic sample resumes, allowing examiners to test the system in one click without preparing their own files.
