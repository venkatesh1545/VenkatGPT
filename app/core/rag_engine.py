"""
app/core/rag_engine.py
───────────────────────
RAG pipeline orchestrator.
Handles: query embedding → retrieval → repo intelligence → context assembly.
"""

import logging
import numpy as np
from app.vectorstore.index_manager import IndexManager
from app.ingestion.embedder import Embedder
from app.ingestion.github_fetcher import GitHubFetcher
from app.core.persona_guard import PersonaGuard
from app.config import settings

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self, index_manager: IndexManager, portfolio: dict):
        self.index_manager = index_manager
        self.portfolio = portfolio
        self.embedder = Embedder()
        self.github = GitHubFetcher()
        self.guard = PersonaGuard()

    async def retrieve(
        self,
        query: str,
        mode: str = "hr",
        top_k: int = None,
    ) -> list[str]:
        """
        Full retrieval pipeline:
        1. Embed query
        2. Search portfolio index
        3. Search resume index
        4. If project name detected → trigger Repo Intelligence
        5. Merge, deduplicate, return formatted context strings
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        query_embedding = self.embedder.embed(query)

        # ── Base retrieval ─────────────────────────────────────────────
        portfolio_results = self.index_manager.portfolio_index.search(
            query_embedding, k=top_k
        )
        resume_results = self.index_manager.resume_index.search(
            query_embedding, k=3
        )

        all_results = portfolio_results + resume_results

        # ── Repo Intelligence ──────────────────────────────────────────
        repo_slug = self.guard.detect_project_name(query, self.portfolio)
        if repo_slug:
            logger.info(f"Repo Intelligence triggered: {repo_slug}")
            repo_results = await self._get_repo_chunks(repo_slug, query_embedding, k=6)
            # Repo results get higher priority — prepend them
            all_results = repo_results + all_results

        # ── Deduplicate and format ─────────────────────────────────────
        context_strings = self._format_context(all_results)

        logger.info(
            f"Retrieval complete: {len(context_strings)} context chunks "
            f"(portfolio: {len(portfolio_results)}, resume: {len(resume_results)}, "
            f"repo: {len(all_results) - len(portfolio_results) - len(resume_results)})"
        )
        return context_strings

    async def _get_repo_chunks(
        self, slug: str, query_embedding: np.ndarray, k: int = 6
    ) -> list[dict]:
        """Get repo chunks from cache or fetch fresh from GitHub."""
        repo_index = self.index_manager.get_repo_index(slug)

        if repo_index is None:
            # Cache miss — fetch from GitHub
            logger.info(f"Cache miss for {slug} — fetching from GitHub...")
            repo_chunks = await self.github.fetch_repo_chunks(slug)
            repo_index = self.index_manager.build_repo_index(slug, repo_chunks)

        return repo_index.search(query_embedding, k=k)

    def _format_context(self, results: list[dict]) -> list[str]:
        """
        Deduplicate by text, format for prompt injection.
        Returns list of strings like "[Source: ...]\n{text}"
        """
        seen_texts = set()
        formatted = []
        for r in results:
            text = r.get("text", "").strip()
            if not text or text in seen_texts:
                continue
            seen_texts.add(text)
            source = r.get("source", "portfolio")
            score = r.get("score", 0)
            formatted.append(f"[{source}]\n{text}")

        # Cap total context to avoid token overflow
        # Rough estimate: 4 chars per token, keep under MAX_CONTEXT_TOKENS
        total_chars = 0
        capped = []
        char_limit = settings.MAX_CONTEXT_TOKENS * 4
        for chunk in formatted:
            if total_chars + len(chunk) > char_limit:
                break
            capped.append(chunk)
            total_chars += len(chunk)

        return capped
