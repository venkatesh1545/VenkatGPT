"""
app/vectorstore/index_manager.py
──────────────────────────────────
Manages all FAISS indexes:
- portfolio index (from portfolio.json)
- resume index (from resume.pdf)
- per-repo indexes (GitHub Repo Intelligence, cached)
"""

import logging
from pathlib import Path
from app.vectorstore.faiss_store import FAISSStore
from app.ingestion.embedder import Embedder
from app.config import settings

logger = logging.getLogger(__name__)


class IndexManager:
    def __init__(self):
        self.indexes_dir = Path(settings.INDEXES_DIR)
        self.portfolio_index: FAISSStore | None = None
        self.resume_index: FAISSStore | None = None
        self._repo_indexes: dict[str, FAISSStore] = {}  # slug → FAISSStore
        self.embedder = Embedder()

    def load_all(self) -> None:
        """Load all persistent indexes at startup."""
        self.portfolio_index = self._load_or_empty("portfolio")
        self.resume_index = self._load_or_empty("resume")

        # Load any cached repo indexes
        github_cache = self.indexes_dir / "github_cache"
        if github_cache.exists():
            for repo_dir in github_cache.iterdir():
                if repo_dir.is_dir():
                    try:
                        slug = repo_dir.name.replace("__", "/")
                        self._repo_indexes[slug] = FAISSStore.load(str(repo_dir))
                        logger.info(f"Loaded cached repo index: {slug}")
                    except Exception as e:
                        logger.warning(f"Could not load repo cache {repo_dir}: {e}")

        logger.info(
            f"Indexes ready — portfolio: {self.portfolio_index.size} vecs, "
            f"resume: {self.resume_index.size} vecs, "
            f"repos cached: {len(self._repo_indexes)}"
        )

    def build_portfolio_index(self, chunks: list[dict]) -> None:
        """Build and save portfolio index from chunks."""
        store = FAISSStore()
        store.add(chunks, self.embedder)
        store.save(str(self.indexes_dir / "portfolio"))
        self.portfolio_index = store
        logger.info(f"Portfolio index built: {store.size} vectors")

    def build_resume_index(self, chunks: list[dict]) -> None:
        """Build and save resume index from chunks."""
        if not chunks:
            logger.warning("No resume chunks — resume index will be empty.")
            self.resume_index = FAISSStore()
            return
        store = FAISSStore()
        store.add(chunks, self.embedder)
        store.save(str(self.indexes_dir / "resume"))
        self.resume_index = store
        logger.info(f"Resume index built: {store.size} vectors")

    def build_repo_index(self, slug: str, chunks: list[dict]) -> FAISSStore:
        """Build and cache a repo-specific FAISS index."""
        store = FAISSStore()
        if chunks:
            store.add(chunks, self.embedder)
        # Save with slug encoded (replace / with __)
        safe_name = slug.replace("/", "__")
        cache_path = str(self.indexes_dir / "github_cache" / safe_name)
        store.save(cache_path)
        self._repo_indexes[slug] = store
        logger.info(f"Repo index built and cached: {slug} ({store.size} vectors)")
        return store

    def get_repo_index(self, slug: str) -> FAISSStore | None:
        return self._repo_indexes.get(slug)

    def _load_or_empty(self, name: str) -> FAISSStore:
        """Try to load an index; return empty store if not found."""
        path = str(self.indexes_dir / name)
        try:
            return FAISSStore.load(path)
        except FileNotFoundError:
            logger.warning(f"Index '{name}' not found. Run scripts/build_index.py first.")
            return FAISSStore()
