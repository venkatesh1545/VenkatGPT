"""
app/vectorstore/faiss_store.py
───────────────────────────────
FAISS vector store wrapper.
Uses IndexFlatIP (inner product = cosine similarity on normalized vectors).
"""

import faiss
import numpy as np
import pickle
import logging
from pathlib import Path
from app.ingestion.embedder import Embedder
from app.config import settings

logger = logging.getLogger(__name__)


class FAISSStore:
    def __init__(self, dimension: int = None):
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        # IndexFlatIP = exact search with inner product
        # On L2-normalized vectors, inner product == cosine similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata: list[dict] = []  # Parallel list — metadata[i] corresponds to vector i

    def add(self, chunks: list[dict], embedder: Embedder = None) -> None:
        """
        Embed chunks and add to FAISS index.
        chunks: list of {"text": ..., "source": ..., "type": ...}
        """
        if not chunks:
            return

        _embedder = embedder or Embedder()
        texts = [c["text"] for c in chunks]
        embeddings = _embedder.embed_batch(texts)  # Already L2-normalized

        self.index.add(embeddings)
        self.metadata.extend(chunks)
        logger.info(f"Added {len(chunks)} vectors. Total: {self.index.ntotal}")

    def search(self, query_embedding: np.ndarray, k: int = 8) -> list[dict]:
        """
        Find top-K most similar chunks.
        Returns list of {"text": ..., "source": ..., "score": float}
        """
        if self.index.ntotal == 0:
            return []

        q = query_embedding.reshape(1, -1).astype("float32")
        # Normalize query too (should already be normalized from embedder)
        faiss.normalize_L2(q)

        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(q, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if score < settings.SIMILARITY_THRESHOLD:
                continue
            chunk = dict(self.metadata[idx])
            chunk["score"] = float(score)
            results.append(chunk)

        return results

    def search_text(self, query_embedding: np.ndarray, k: int = 8) -> list[str]:
        """Convenience: returns just formatted text strings for prompt injection."""
        results = self.search(query_embedding, k)
        return [
            f"[Source: {r['source']} | Relevance: {r['score']:.2f}]\n{r['text']}"
            for r in results
        ]

    def save(self, dir_path: str) -> None:
        """Save FAISS index + metadata to disk."""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "index.faiss"))
        with open(path / "metadata.pkl", "wb") as f:
            pickle.dump(self.metadata, f)
        logger.info(f"Saved FAISS store to {dir_path} ({self.index.ntotal} vectors)")

    @classmethod
    def load(cls, dir_path: str) -> "FAISSStore":
        """Load FAISS index + metadata from disk."""
        path = Path(dir_path)
        if not (path / "index.faiss").exists():
            raise FileNotFoundError(f"No FAISS index at {dir_path}")

        store = cls()
        store.index = faiss.read_index(str(path / "index.faiss"))
        with open(path / "metadata.pkl", "rb") as f:
            store.metadata = pickle.load(f)
        logger.info(f"Loaded FAISS store from {dir_path} ({store.index.ntotal} vectors)")
        return store

    @property
    def size(self) -> int:
        return self.index.ntotal
