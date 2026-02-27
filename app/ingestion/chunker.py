"""
app/ingestion/chunker.py
────────────────────────
Smart text chunking strategies for different content types.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import logging

logger = logging.getLogger(__name__)


class SmartChunker:
    def __init__(self):
        # Markdown / README — split on headings first
        self.markdown_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " "],
        )

        # Code files — split on class/function boundaries
        self.code_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=["\nclass ", "\ndef ", "\nasync def ", "\n\n", "\n"],
        )

        # Prose (resume, descriptions) — split on sentences
        self.prose_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=60,
            separators=["\n\n", ". ", "\n", " "],
        )

        # JSON/portfolio data — split on double newlines
        self.json_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=["\n\n", "\n"],
        )

    def chunk_markdown(self, text: str, source: str) -> list[dict]:
        chunks = self.markdown_splitter.split_text(text)
        return [
            {"text": c.strip(), "source": source, "type": "markdown"}
            for c in chunks
            if c.strip()
        ]

    def chunk_code(self, text: str, source: str, language: str = "python") -> list[dict]:
        chunks = self.code_splitter.split_text(text)
        return [
            {"text": c.strip(), "source": source, "type": "code", "lang": language}
            for c in chunks
            if c.strip()
        ]

    def chunk_prose(self, text: str, source: str) -> list[dict]:
        chunks = self.prose_splitter.split_text(text)
        return [
            {"text": c.strip(), "source": source, "type": "prose"}
            for c in chunks
            if c.strip()
        ]

    def chunk_json_text(self, text: str, source: str) -> list[dict]:
        chunks = self.json_splitter.split_text(text)
        return [
            {"text": c.strip(), "source": source, "type": "portfolio"}
            for c in chunks
            if c.strip()
        ]
