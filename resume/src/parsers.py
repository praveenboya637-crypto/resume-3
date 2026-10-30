"""
AI Resume Screening and Job Matching System
File Parsers: Extract and clean text from PDF and DOCX documents with robust error handling and OCR detection.
"""

import io
import os
import re
from typing import Dict, Any, Tuple, Optional
import pymupdf  # PyMuPDF
import docx


def clean_text(text: str) -> str:
    """
    Cleans and normalizes extracted text for accurate NLP processing.
    - Preserves letters, digits, and programming symbols (C++, C#, .NET).
    - Replaces unicode bullets, non-breaking spaces, and ligatures.
    - Normalizes multiple spaces and blank lines.
    """
    if not text or not isinstance(text, str):
        return ""

    # Replace non-breaking spaces and zero-width spaces
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")

    # Replace common unicode bullet points and fancy dashes with standard characters
    text = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219\u25AA\u25AB\u2042]", " - ", text)
    text = re.sub(r"[\u2013\u2014]", "-", text)
    text = re.sub(r"[\u201C\u201D\u201E\u00AB\u00BB]", '"', text)
    text = re.sub(r"[\u2018\u2019\u201A\u201B`]", "'", text)

    # Normalize carriage returns and tabs
    text = text.replace("\r", "\n").replace("\t", " ")

    # Remove non-printable control characters (except newline)
    text = "".join(ch for ch in text if ch == "\n" or (32 <= ord(ch) <= 126) or ord(ch) > 160)

    # Collapse multiple consecutive newlines and spaces
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)

    return text.strip()


def extract_metadata_heuristics(text: str) -> Dict[str, Any]:
    """
    Extracts basic contact heuristics (email, phone, links) if present.
    Note: These are informational display hints and NOT used in scoring.
    """
    if not text:
        return {
            "email": None,
            "phone": None,
            "linkedin": None,
            "github": None,
            "word_count": 0,
            "char_count": 0
        }

    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    linkedin_match = re.search(r"(linkedin\.com/in/[a-zA-Z0-9_-]+)", text, re.IGNORECASE)
    github_match = re.search(r"(github\.com/[a-zA-Z0-9_-]+)", text, re.IGNORECASE)

    words = text.split()
    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "linkedin": linkedin_match.group(0) if linkedin_match else None,
        "github": github_match.group(0) if github_match else None,
        "word_count": len(words),
        "char_count": len(text)
    }


def extract_text_from_pdf(file_source: Any) -> Tuple[str, int, Optional[str], bool]:
    """
    Extracts text from a PDF file using PyMuPDF.
    Supports either a file path (str) or a file-like byte buffer (BytesIO or Streamlit UploadedFile).
    Attempts OCR fallback for scanned/image-only PDFs if Tesseract is available.
    
    Returns:
        (extracted_text: str, page_count: int, error_message: Optional[str], is_scanned: bool)
    """
    doc = None
    try:
        # 1. Open document from file path, bytes, or file-like buffer
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                return "", 0, f"File not found: {file_source}", False
            if os.path.getsize(file_source) == 0:
                return "", 0, "Uploaded PDF file is empty (0 bytes).", False
            doc = pymupdf.open(file_source)
        elif isinstance(file_source, bytes):
            if len(file_source) == 0:
                return "", 0, "Uploaded PDF file is empty (0 bytes).", False
            doc = pymupdf.open(stream=file_source, filetype="pdf")
        elif hasattr(file_source, "read"):
            content = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            if not content or len(content) == 0:
                return "", 0, "Uploaded PDF file is empty (0 bytes).", False
            doc = pymupdf.open(stream=content, filetype="pdf")
        else:
            return "", 0, f"Unsupported file source type: {type(file_source)}", False

        # 2. Check encryption / password protection
        if doc.is_encrypted:
            page_count = len(doc)
            doc.close()
            return "", page_count, "PDF is password-protected or encrypted. Please remove password protection before uploading.", False

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            return "", 0, "The PDF document contains 0 pages.", False

        # 3. Extract standard selectable text
        text_parts = []
        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                text_parts.append(page_text.strip())

        combined_text = "\n".join(text_parts).strip()

        # 4. If no text was found, handle scanned/image PDF with OCR fallback
        is_scanned = False
        if not combined_text:
            is_scanned = True
            ocr_text_parts = []
            ocr_error = None
            try:
                for page_idx in range(page_count):
                    page = doc[page_idx]
                    tp = page.get_textpage_ocr(language="eng", dpi=150, full=True)
                    ocr_page_text = tp.extractText()
                    if ocr_page_text and ocr_page_text.strip():
                        ocr_text_parts.append(ocr_page_text.strip())
                if ocr_text_parts:
                    combined_text = "\n".join(ocr_text_parts).strip()
            except Exception as e:
                ocr_error = str(e)

            if not combined_text:
                doc.close()
                if ocr_error and ("tessdata" in ocr_error.lower() or "tesseract" in ocr_error.lower()):
                    return "", page_count, "Scanned PDF detected (no selectable text). To enable OCR extraction for image-based PDFs, install Tesseract-OCR on the system.", True
                return "", page_count, "No selectable or readable text found in PDF. The document may be empty or an image-only scan without OCR.", True

        doc.close()
        return combined_text, page_count, None, is_scanned

    except pymupdf.FileDataError as e:
        if doc is not None:
            doc.close()
        return "", 0, f"Corrupted or invalid PDF structure: {str(e)}", False
    except Exception as e:
        if doc is not None:
            doc.close()
        return "", 0, f"Error parsing PDF: {str(e)}", False


def extract_text_from_docx(file_source: Any) -> Tuple[str, int, Optional[str]]:
    """
    Extracts text from a DOCX file using python-docx.
    Supports either a file path (str) or a file-like byte buffer (BytesIO or Streamlit UploadedFile).
    
    Returns:
        (extracted_text, paragraph_count, error_message)
    """
    try:
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                return "", 0, f"File not found: {file_source}"
            if os.path.getsize(file_source) == 0:
                return "", 0, "Uploaded DOCX file is empty (0 bytes)."
            doc = docx.Document(file_source)
        elif hasattr(file_source, "read"):
            content = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            if not content or len(content) == 0:
                return "", 0, "Uploaded DOCX file is empty (0 bytes)."
            doc = docx.Document(io.BytesIO(content))
        elif isinstance(file_source, bytes):
            if not file_source or len(file_source) == 0:
                return "", 0, "Uploaded DOCX byte data is empty (0 bytes)."
            doc = docx.Document(io.BytesIO(file_source))
        else:
            return "", 0, f"Unsupported file source type: {type(file_source)}"

        text_parts = []
        # Extract from normal paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())

        # Also extract from tables (resumes frequently use tables for two-column layouts)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    text_parts.append(" | ".join(row_cells))

        combined_text = "\n".join(text_parts).strip()
        if not combined_text:
            return "", len(doc.paragraphs), "The DOCX document does not contain any readable text."

        return combined_text, len(doc.paragraphs), None

    except docx.opc.exceptions.PackageNotFoundError:
        return "", 0, "Invalid or corrupted DOCX file: Not a valid Word document package."
    except Exception as e:
        return "", 0, f"Error parsing DOCX: {str(e)}"


def parse_resume(file_obj_or_path: Any, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Unified entry point for parsing any supported resume file (PDF, DOCX, TXT).
    Returns a structured dictionary with text, status, page count, and metadata.
    """
    if filename is None:
        filename = getattr(file_obj_or_path, "name", "resume_document")

    ext = filename.lower().split(".")[-1] if "." in filename else ""

    result: Dict[str, Any] = {
        "filename": filename,
        "extension": ext,
        "status": "error",
        "raw_text": "",
        "clean_text": "",
        "error_message": None,
        "page_or_para_count": 0,
        "is_scanned": False,
        "metadata": {}
    }

    if ext == "pdf":
        raw_text, count, err, is_scanned = extract_text_from_pdf(file_obj_or_path)
        result["is_scanned"] = is_scanned
    elif ext in ["docx", "doc"]:
        if ext == "doc":
            result["error_message"] = "Legacy .doc format is not supported. Please save or convert the file to .docx or .pdf."
            return result
        raw_text, count, err = extract_text_from_docx(file_obj_or_path)
    elif ext in ["txt", "md"]:
        try:
            if hasattr(file_obj_or_path, "read"):
                content = file_obj_or_path.read()
                if isinstance(content, bytes):
                    raw_text = content.decode("utf-8", errors="ignore")
                else:
                    raw_text = str(content)
                if hasattr(file_obj_or_path, "seek"):
                    file_obj_or_path.seek(0)
            else:
                with open(file_obj_or_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
            count = len(raw_text.splitlines())
            err = None if raw_text.strip() else "Empty text file."
        except Exception as e:
            raw_text, count, err = "", 0, str(e)
    else:
        result["error_message"] = f"Unsupported file type: .{ext}. Please upload a PDF or DOCX file."
        return result

    if err:
        result["error_message"] = err
        result["status"] = "error"
        return result

    cleaned = clean_text(raw_text)
    if not cleaned:
        result["error_message"] = "Document extracted 0 readable characters."
        result["status"] = "empty"
        return result

    result["status"] = "success"
    result["raw_text"] = raw_text
    result["clean_text"] = cleaned
    result["page_or_para_count"] = count
    result["metadata"] = extract_metadata_heuristics(cleaned)
    return result
