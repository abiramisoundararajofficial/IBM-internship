"""RAG utilities: embeddings + FAISS-based retrieval for resumes.

This module builds a lightweight in-memory FAISS index using
`sentence_transformers` for embeddings and `faiss` for nearest-neighbor search.

Keep implementations local to avoid external LLM usage; the retrieval
returns resume paths and short snippets for the UI to display.
"""

from typing import List, Dict, Tuple


def build_resume_index(resume_paths: List[str], model_name: str = "all-MiniLM-L6-v2"):
    """Build and return (index, metadata, model) for given resume_paths.

    - `index` is a FAISS IndexFlatIP over L2-normalized embeddings.
    - `metadata` is a list of dicts with `path` and `text_snippet`.
    - `model` is the SentenceTransformer instance for reuse.
    """
    if not resume_paths:
        return None, [], None

    # Lazy imports to avoid heavy imports at module import time
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    from .resume_parser import extract_text_from_pdf

    model = SentenceTransformer(model_name)

    texts: List[str] = []
    for p in resume_paths:
        try:
            txt = extract_text_from_pdf(p)
        except Exception:
            txt = ""
        texts.append(txt)

    embeddings = model.encode(texts, show_progress_bar=False)
    embeddings = np.array(embeddings).astype("float32")

    # normalize for cosine-sim via inner product
    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    metadata = []
    for i, p in enumerate(resume_paths):
        snippet = texts[i][:1000] if texts[i] else ""
        metadata.append({"path": p, "text_snippet": snippet})

    return index, metadata, model


def search_resumes(query: str, resume_paths: List[str], k: int = 5, model_name: str = "all-MiniLM-L6-v2") -> List[Dict[str, object]]:
    """Search resumes for a query and return top-k results.

    Each result: {path, score, snippet}
    Scores are cosine similarities in [ -1 .. 1 ] (higher is better).
    """
    if not query or not resume_paths:
        return []

    index, metadata, model = build_resume_index(resume_paths, model_name=model_name)
    if index is None:
        return []

    import numpy as np

    qemb = model.encode([query], show_progress_bar=False)
    qemb = np.array(qemb).astype("float32")
    faiss.normalize_L2(qemb)

    D, I = index.search(qemb, min(k, index.ntotal))
    results = []
    for score, idx in zip(D[0], I[0]):
        meta = metadata[int(idx)]
        results.append({"path": meta["path"], "score": float(score), "snippet": meta.get("text_snippet", "")})

    return results

