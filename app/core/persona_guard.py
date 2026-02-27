"""
app/core/persona_guard.py
──────────────────────────
Persona enforcement layer.
- Builds mode-specific system prompts
- Detects off-topic questions
- Returns redirect messages
"""

import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

OFF_TOPIC_PATTERNS = [
    # Food / lifestyle
    "recipe", "cooking", "food", "restaurant",
    # Sports
    "cricket score", "football result", "match result", "sports news",
    # Entertainment
    "movie review", "song lyrics", "tv show", "web series",
    # Finance
    "stock price", "crypto price", "share market",
    # News / politics
    "breaking news", "election result", "weather forecast",
    # Trivial
    "joke", "riddle", "fun fact", "horoscope",
]


class PersonaGuard:
    def __init__(self):
        prompts_dir = Path(settings.PROMPTS_DIR)
        self.base_prompt = self._load(prompts_dir / "system_base.txt")
        self.mode_prompts = {
            "hr": self._load(prompts_dir / "hr_mode.txt"),
            "technical": self._load(prompts_dir / "technical_mode.txt"),
            "summary": self._load(prompts_dir / "summary_mode.txt"),
        }

    def _load(self, path: Path) -> str:
        if path.exists():
            return path.read_text(encoding="utf-8")
        logger.warning(f"Prompt file not found: {path}")
        return ""

    def build_system_prompt(self, mode: str = "hr") -> str:
        """Combine base persona prompt with mode-specific overlay."""
        mode_overlay = self.mode_prompts.get(mode, self.mode_prompts["hr"])
        return f"{self.base_prompt}\n\n{mode_overlay}"

    def is_off_topic(self, query: str) -> bool:
        """Lightweight off-topic filter before hitting Claude."""
        query_lower = query.lower()
        return any(pattern in query_lower for pattern in OFF_TOPIC_PATTERNS)

    def get_redirect_message(self, query: str) -> str:
        return (
            "That's a bit outside my professional portfolio scope! "
            "But I'd love to chat about my projects, tech stack, or career journey. "
            "What would you like to know about my work?"
        )

    def detect_project_name(self, query: str, portfolio: dict) -> str | None:
        """
        Fuzzy-match query against known project names.
        Returns the matching project slug (for GitHub API fetch) or None.
        """
        projects = portfolio.get("projects", [])
        query_lower = query.lower()
        for project in projects:
            name = project.get("name", "").lower()
            slug = project.get("slug", "").lower()
            github_repo = project.get("github_repo", "").lower()
            if name in query_lower or slug in query_lower:
                return project.get("github_repo", "")
        return None
