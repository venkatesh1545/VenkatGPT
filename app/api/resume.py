"""
app/api/resume.py
──────────────────
Resume endpoints:
- GET /resume/download  → redirect to download URL
- GET /resume/view      → redirect to viewable URL
- GET /resume/summary   → AI-generated resume summary
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from app.config import settings
from app.core.claude_client import complete_claude
from app.core.persona_guard import PersonaGuard

logger = logging.getLogger(__name__)
router = APIRouter()
_guard = PersonaGuard()


@router.get("/resume/download")
async def resume_download():
    """Redirect to resume PDF download URL."""
    if not settings.RESUME_DOWNLOAD_URL:
        return JSONResponse(
            {"message": "Resume download link not configured. Please contact me directly."},
            status_code=404,
        )
    return RedirectResponse(url=settings.RESUME_DOWNLOAD_URL)


@router.get("/resume/view")
async def resume_view():
    """Redirect to resume view URL (e.g. S3 public URL or Google Drive viewer)."""
    if not settings.RESUME_VIEW_URL:
        return JSONResponse(
            {"message": "Resume view link not configured. Please contact me directly."},
            status_code=404,
        )
    return RedirectResponse(url=settings.RESUME_VIEW_URL)


@router.get("/resume/summary")
async def resume_summary(request: Request):
    """AI-generated resume summary using portfolio context."""
    rag = request.app.state.rag_engine
    portfolio = request.app.state.portfolio

    identity = portfolio.get("identity", {})
    skills = portfolio.get("skills", {})
    experience = portfolio.get("experience", [])
    projects = portfolio.get("projects", [])
    certs = portfolio.get("certifications", [])

    # Build a rich context directly from portfolio
    context = f"""
Name: {identity.get('full_name', identity.get('name', 'Venkat'))}
Role: {identity.get('tagline', '')}
Summary: {identity.get('summary', '')}
Years of Experience: {identity.get('years_of_experience', '')}

Top Skills: {', '.join(skills.get('ai_ml', [])[:5] + skills.get('backend', [])[:3])}

Key Projects: {', '.join(p['name'] for p in projects[:3])}

Experience: {'; '.join(f"{e['title']} at {e['company']}" for e in experience)}

Certifications: {', '.join(c['name'] for c in certs)}
"""

    system_prompt = _guard.build_system_prompt("hr")
    query = "Give a comprehensive, structured resume summary covering my background, skills, key projects, and career highlights."

    summary = await complete_claude(system_prompt, query, [context])

    return {
        "name": identity.get("full_name", "Venkat"),
        "summary": summary,
        "download_url": settings.RESUME_DOWNLOAD_URL or None,
        "view_url": settings.RESUME_VIEW_URL or None,
    }
