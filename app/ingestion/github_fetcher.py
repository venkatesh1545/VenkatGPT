"""
app/ingestion/github_fetcher.py
────────────────────────────────
GitHub API integration for Repo Intelligence Mode.
Fetches README + relevant code files, returns chunks.
"""

import httpx
import base64
import logging
from app.config import settings
from app.ingestion.chunker import SmartChunker

logger = logging.getLogger(__name__)

RELEVANT_EXTENSIONS = {".py", ".ts", ".js", ".go", ".md", ".yaml", ".yml", ".json", ".sh", ".tsx", ".jsx"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "dist", "build", ".next", "venv", "env", ".venv"}
MAX_FILE_SIZE_BYTES = 80 * 1024  # 80 KB max per file
MAX_FILES_TO_FETCH = 25


class GitHubFetcher:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        self.base = "https://api.github.com"
        self.chunker = SmartChunker()

    async def fetch_repo_chunks(self, repo_slug: str) -> list[dict]:
        """
        Main entry point.
        repo_slug: "username/repo-name"
        Returns list of chunk dicts with text + source metadata.
        """
        logger.info(f"Fetching GitHub repo: {repo_slug}")
        chunks = []

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=20.0) as client:
                # 1. README — highest priority
                readme = await self._fetch_readme(client, repo_slug)
                if readme:
                    readme_chunks = self.chunker.chunk_markdown(readme, f"github/{repo_slug}/README.md")
                    chunks.extend(readme_chunks)
                    logger.info(f"README: {len(readme_chunks)} chunks")

                # 2. File tree
                tree = await self._fetch_tree(client, repo_slug)
                relevant_files = self._filter_files(tree)
                logger.info(f"Relevant files found: {len(relevant_files)}")

                # 3. Fetch file contents
                fetched = 0
                for file_path in relevant_files[:MAX_FILES_TO_FETCH]:
                    if file_path.lower().endswith(".md"):
                        continue  # Already got README, skip other md for now
                    content = await self._fetch_file(client, repo_slug, file_path)
                    if content:
                        ext = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ""
                        file_chunks = self.chunker.chunk_code(
                            content,
                            source=f"github/{repo_slug}/{file_path}",
                            language=ext.lstrip("."),
                        )
                        chunks.extend(file_chunks)
                        fetched += 1

                logger.info(f"Repo {repo_slug}: {fetched} files → {len(chunks)} total chunks")

        except httpx.TimeoutException:
            logger.warning(f"GitHub fetch timeout for {repo_slug}")
        except Exception as e:
            logger.error(f"GitHub fetch failed for {repo_slug}: {e}")

        return chunks

    async def _fetch_readme(self, client: httpx.AsyncClient, repo_slug: str) -> str | None:
        try:
            r = await client.get(f"{self.base}/repos/{repo_slug}/readme")
            if r.status_code == 200:
                data = r.json()
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            pass
        return None

    async def _fetch_tree(self, client: httpx.AsyncClient, repo_slug: str) -> list[dict]:
        try:
            r = await client.get(f"{self.base}/repos/{repo_slug}/git/trees/HEAD?recursive=1")
            if r.status_code == 200:
                return r.json().get("tree", [])
        except Exception:
            pass
        return []

    def _filter_files(self, tree: list[dict]) -> list[str]:
        result = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            size = item.get("size", 0)
            # Skip if in a skip directory
            if any(skip in path.split("/") for skip in SKIP_DIRS):
                continue
            # Check extension
            if not any(path.endswith(ext) for ext in RELEVANT_EXTENSIONS):
                continue
            # Size check
            if size > MAX_FILE_SIZE_BYTES:
                continue
            result.append(path)
        # Sort: put main files first, then by depth
        result.sort(key=lambda p: (p.count("/"), p))
        return result

    async def _fetch_file(self, client: httpx.AsyncClient, repo_slug: str, file_path: str) -> str | None:
        try:
            r = await client.get(f"{self.base}/repos/{repo_slug}/contents/{file_path}")
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and "content" in data:
                    return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            pass
        return None
