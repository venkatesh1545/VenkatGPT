"""
app/core/claude_client.py
──────────────────────────
Google Gemini API integration with identity injection.
"""

import google.generativeai as genai
import logging
import asyncio
import json
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-04-17")

if not _GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in .env file!")
else:
    genai.configure(api_key=_GEMINI_API_KEY)
    logger.info(f"Gemini configured. Model: {_MODEL_NAME}")


def _load_identity_block() -> str:
    try:
        with open("data/portfolio.json", "r") as f:
            p = json.load(f)

        identity = p.get("identity", {})
        skills = p.get("skills", {})
        projects = p.get("projects", [])
        certs = p.get("certifications", [])
        achievements = p.get("achievements", [])

        project_lines = []
        for proj in projects:
            line = f"  - {proj['name']}: {proj.get('description', '')[:100]}"
            if proj.get("github_url"):
                line += f" | GitHub: {proj['github_url']}"
            if proj.get("demo_url"):
                line += f" | Demo: {proj['demo_url']}"
            project_lines.append(line)

        cert_lines = [
            f"  - {c['name']} by {c['issuer']} ({c.get('year', '')})"
            for c in certs
        ]

        ach_lines = [
            f"  - {a['title']} ({a.get('year', '')})"
            for a in achievements
        ]

        github_username = identity.get('github', '').replace('https://github.com/', '') if identity.get('github') else ''
        wp = identity.get('work_preferences', {})

        block = f"""
VENKAT'S CORE IDENTITY (Always use these exact facts — never say you don't know these):
Full Name:     {identity.get('full_name', identity.get('name', ''))}
Role:          {identity.get('tagline', '')}
Email:         {identity.get('email', '')}
Location:      {identity.get('location', '')}
GitHub URL:    {identity.get('github', '')}
GitHub User:   {github_username}
LinkedIn:      {identity.get('linkedin', '')}
Portfolio:     {identity.get('portfolio_url', '')}
Experience:    {identity.get('years_of_experience', '')} years

WORK PREFERENCES (Answer directly and confidently — do NOT say "I don't have info"):
Open to Relocate:  {wp.get('relocation', 'Yes — open to relocate anywhere in India or abroad')}
Remote Work:       {wp.get('remote_work', 'Yes — fully comfortable with remote, hybrid, or on-site')}
Preferred Cities:  {', '.join(wp.get('preferred_locations', ['Bangalore', 'Hyderabad', 'Remote', 'Any location']))}
Notice Period:     {wp.get('notice_period', 'Immediate to 30 days')}
Employment Type:   {', '.join(wp.get('employment_type', ['Full-time', 'Contract']))}
Key Message:       {wp.get('open_to', 'Location has never been a barrier — what matters is great work, great team, and meaningful problems.')}

Top AI/ML Skills: {', '.join(skills.get('ai_ml', [])[:6])}
Backend Skills:   {', '.join(skills.get('backend', [])[:5])}
Cloud Skills:     {', '.join(skills.get('cloud', [])[:3])}

Projects (with links):
{chr(10).join(project_lines)}

Certifications:
{chr(10).join(cert_lines)}

Key Achievements:
{chr(10).join(ach_lines[:3])}""".strip()
        return block
    except Exception as e:
        logger.warning(f"Could not load identity block: {e}")
        return ""


_IDENTITY_BLOCK = _load_identity_block()


def _build_augmented_message(user_query: str, context_chunks: list[str]) -> str:
    context_block = "\n\n".join(context_chunks) if context_chunks else "(No additional context retrieved)"

    return f"""
{_IDENTITY_BLOCK}

---
ADDITIONAL RETRIEVED CONTEXT FROM PORTFOLIO DATABASE:
{context_block}
---

CRITICAL RULES:
- When user asks for GitHub/LinkedIn/demo/portfolio URLs → provide the EXACT URLs from identity block above
- When user asks for GitHub username → extract it from the GitHub URL above
- NEVER say "I don't have that information" for anything shown in the identity block
- Always speak in first person as Venkat
- For unknown topics, use the Unknown Question Protocol

USER QUESTION: {user_query}
""".strip()


async def stream_claude(
    system_prompt: str,
    user_query: str,
    context_chunks: list[str],
) -> AsyncGenerator[str, None]:
    if not _GEMINI_API_KEY:
        yield "GEMINI_API_KEY missing in .env file. Please add it and restart."
        return

    try:
        model = genai.GenerativeModel(
            model_name=_MODEL_NAME,
            system_instruction=system_prompt,
        )

        augmented_message = _build_augmented_message(user_query, context_chunks)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(augmented_message, stream=True)
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        yield "Sorry, something went wrong. Please try again."


async def complete_claude(
    system_prompt: str,
    user_query: str,
    context_chunks: list[str],
) -> str:
    full_response = ""
    async for token in stream_claude(system_prompt, user_query, context_chunks):
        full_response += token
    return full_response