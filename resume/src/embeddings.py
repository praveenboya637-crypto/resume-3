"""
AI Resume Screening and Job Matching System
Sentence Embeddings & Semantic Similarity Engine using Sentence Transformers and Scikit-Learn.
"""

from typing import Tuple, Optional, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from src.constants import DEFAULT_MODEL_NAME

# Global cache for standalone scripts/testing outside Streamlit
_GLOBAL_MODEL_CACHE: Optional[Any] = None
_MODEL_BACKEND: str = "sentence-transformers"


def load_sentence_transformer_model(model_name: str = DEFAULT_MODEL_NAME):
    """
    Loads and caches the SentenceTransformer model locally.
    Uses 'all-MiniLM-L6-v2', a fast, lightweight, state-of-the-art embedding model
    that runs 100% locally on CPU without requiring any paid API key.
    """
    global _GLOBAL_MODEL_CACHE, _MODEL_BACKEND

    if _GLOBAL_MODEL_CACHE is not None:
        return _GLOBAL_MODEL_CACHE, _MODEL_BACKEND

    try:
        from sentence_transformers import SentenceTransformer
        # Loads local weights if already cached in ~/.cache/huggingface, or downloads them once
        model = SentenceTransformer(model_name)
        _GLOBAL_MODEL_CACHE = model
        _MODEL_BACKEND = "sentence-transformers"
        return model, "sentence-transformers"
    except Exception as e:
        print(f"[Warning] Could not initialize SentenceTransformer ({e}). Falling back to TF-IDF.")
        _GLOBAL_MODEL_CACHE = None
        _MODEL_BACKEND = "tfidf-fallback"
        return None, "tfidf-fallback"


def compute_semantic_similarity(
    resume_text: str,
    jd_text: str,
    model: Optional[Any] = None,
    backend: Optional[str] = None
) -> Tuple[float, str]:
    """
    Calculates semantic cosine similarity between resume text and job description.
    
    Args:
        resume_text: Cleaned text from candidate resume.
        jd_text: Cleaned text from job description.
        model: Optional pre-loaded SentenceTransformer model instance.
        backend: Optional indicator ('sentence-transformers' or 'tfidf-fallback').
        
    Returns:
        (similarity_score: float [0.0 - 1.0], method_used: str)
    """
    if not resume_text.strip() or not jd_text.strip():
        return 0.0, "empty-text"

    if model is None:
        model, detected_backend = load_sentence_transformer_model()
        backend = backend or detected_backend
    else:
        backend = backend or "sentence-transformers"

    if backend == "sentence-transformers" and model is not None:
        try:
            # Generate dense 384-dimensional contextual embeddings
            embeddings = model.encode(
                [resume_text, jd_text],
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            resume_emb = embeddings[0].reshape(1, -1)
            jd_emb = embeddings[1].reshape(1, -1)

            # Cosine similarity for normalized embeddings is simply dot product
            cos_sim = float(cosine_similarity(resume_emb, jd_emb)[0][0])
            # Bound between 0.0 and 1.0
            cos_sim = max(0.0, min(1.0, cos_sim))
            return round(cos_sim, 4), "sentence-transformers (all-MiniLM-L6-v2)"
        except Exception as e:
            print(f"[Warning] Error during sentence transformer encoding: {e}. Using TF-IDF fallback.")

    # Resilient TF-IDF Fallback
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000
        )
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        sim = max(0.0, min(1.0, sim))
        return round(sim, 4), "TF-IDF + Cosine Similarity (Fallback)"
    except Exception as e:
        return 0.0, f"Error: {str(e)}"


def batch_compute_similarity(
    resumes: list,
    jd_text: str,
    model: Optional[Any] = None
) -> list:
    """
    Computes semantic similarity for multiple resumes in batch mode for efficiency.
    Guarantees that empty or invalid resumes strictly receive a similarity score of 0.0.
    """
    if not resumes or not jd_text.strip():
        return [0.0] * len(resumes)

    # Extract cleaned text strings
    resume_texts = []
    for r in resumes:
        if isinstance(r, dict):
            # Only use text if status is success or text is non-empty
            t = r.get("clean_text", "")
        else:
            t = str(r)
        resume_texts.append(t.strip())

    valid_indices = [idx for idx, t in enumerate(resume_texts) if t]
    similarities = [0.0] * len(resumes)

    if not valid_indices:
        return similarities

    if model is None:
        model, backend = load_sentence_transformer_model()
    else:
        backend = "sentence-transformers"

    if backend == "sentence-transformers" and model is not None:
        try:
            jd_emb = model.encode([jd_text.strip()], show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
            valid_texts = [resume_texts[i] for i in valid_indices]
            res_embs = model.encode(valid_texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
            batch_sims = cosine_similarity(res_embs, jd_emb).flatten()

            for k, orig_idx in enumerate(valid_indices):
                score = float(batch_sims[k])
                similarities[orig_idx] = round(max(0.0, min(1.0, score)), 4)
            return similarities
        except Exception as e:
            print(f"[Warning] Batch transformer failed ({e}). Falling back to individual compute.")

    # Fallback to individual computation
    for i in valid_indices:
        score, _ = compute_semantic_similarity(resume_texts[i], jd_text, model, backend)
        similarities[i] = score
    return similarities
