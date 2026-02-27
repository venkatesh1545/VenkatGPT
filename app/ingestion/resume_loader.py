"""
app/ingestion/resume_loader.py
───────────────────────────────
PDF resume → text extraction → section detection → chunks.
Uses PyMuPDF (fitz) for extraction.
"""

import logging
from pathlib import Path
from app.ingestion.chunker import SmartChunker

logger = logging.getLogger(__name__)

SECTION_HEADERS = {
    "EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE",
    "EDUCATION", "ACADEMIC BACKGROUND",
    "SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES",
    "PROJECTS", "KEY PROJECTS", "ACADEMIC PROJECTS",
    "CERTIFICATIONS", "CERTIFICATES",
    "ACHIEVEMENTS", "AWARDS", "HONORS",
    "SUMMARY", "OBJECTIVE", "PROFILE",
    "PUBLICATIONS", "RESEARCH",
    "VOLUNTEER", "LEADERSHIP", "ACTIVITIES",
    "INTERESTS", "HOBBIES",
}


class ResumeLoader:
    def __init__(self):
        self.chunker = SmartChunker()

    def load_and_chunk(self, pdf_path: str) -> list[dict]:
        """
        Full pipeline: PDF → text → sections → chunks.
        Falls back gracefully if PDF not found (for dev without resume).
        """
        path = Path(pdf_path)
        if not path.exists():
            logger.warning(f"Resume PDF not found at {pdf_path}. Skipping resume indexing.")
            return []

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            pages_text = [page.get_text() for page in doc]
            full_text = "\n".join(pages_text)
            logger.info(f"Resume extracted: {len(full_text)} chars from {len(doc)} pages")
        except Exception as e:
            logger.error(f"Failed to extract resume PDF: {e}")
            return []

        sections = self._detect_sections(full_text)
        chunks = []
        for section_name, section_text in sections.items():
            section_chunks = self.chunker.chunk_prose(
                section_text.strip(),
                source=f"resume/{section_name.lower().replace(' ', '_')}",
            )
            chunks.extend(section_chunks)

        logger.info(f"Resume indexed: {len(chunks)} chunks from {len(sections)} sections")
        return chunks

    def _detect_sections(self, text: str) -> dict[str, str]:
        """Split resume text into named sections."""
        sections: dict[str, str] = {}
        current_section = "OVERVIEW"
        current_lines: list[str] = []

        for line in text.split("\n"):
            stripped = line.strip().upper()
            # Check if this line is a section header
            is_header = (
                stripped in SECTION_HEADERS
                or any(stripped.startswith(h) for h in SECTION_HEADERS)
            )
            if is_header and len(stripped) < 50:
                if current_lines:
                    sections[current_section] = "\n".join(current_lines)
                current_section = line.strip().upper()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections[current_section] = "\n".join(current_lines)

        return sections
