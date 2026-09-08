import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import EMBEDDING_MODEL

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """Returns L2-normalized embeddings, shape (len(texts), dim)."""
    vectors = get_model().encode(texts, convert_to_numpy=True, show_progress_bar=False)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms
