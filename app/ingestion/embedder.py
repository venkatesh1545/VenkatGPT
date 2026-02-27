"""
app/ingestion/embedder.py
─────────────────────────
Unified embedding interface using SentenceTransformers.
Model: all-MiniLM-L6-v2 (384-dim, fast, good quality for semantic search)
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Singleton — loaded once at startup
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded.")
    return _model


class Embedder:
    def __init__(self):
        self.model = get_model()
        self.dimension = settings.EMBEDDING_DIMENSION

    def embed(self, text: str) -> np.ndarray:
        """Embed a single string. Returns (D,) float32 array."""
        vec = self.model.encode(text, normalize_embeddings=True)
        return vec.astype("float32")

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """
        Embed a list of strings.
        Returns (N, D) float32 array, L2-normalized.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype="float32")

        logger.info(f"Embedding {len(texts)} chunks in batches of {batch_size}...")
        vecs = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )
        return vecs.astype("float32")
