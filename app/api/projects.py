"""
app/api/projects.py
────────────────────
Project listing and detail endpoints.
- GET /projects         → list all projects
- GET /projects/{slug}  → single project detail
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from app.core.claude_client import complete_claude
from app.core.persona_guard import PersonaGuard

logger = logging.getLogger(__name__)
router = APIRouter()
_guard = PersonaGuard()


@router.get("/projects")
async def list_projects(request: Request):
    """Return list of all projects from portfolio."""
    portfolio = request.app.state.portfolio
    projects = portfolio.get("projects", [])
    return {
        "count": len(projects),
        "projects": [
            {
                "name": p["name"],
                "slug": p.get("slug", p["name"].lower().replace(" ", "-")),
                "description": p["description"],
                "tech_stack": p.get("tech_stack", []),
                "demo_url": p.get("demo_url", ""),
                "github_url": p.get("github_url", ""),
            }
            for p in projects
        ],
    }


@router.get("/projects/{slug}")
async def get_project(slug: str, request: Request):
    """Return full details for a specific project, optionally with AI explanation."""
    portfolio = request.app.state.portfolio
    projects = portfolio.get("projects", [])

    # Find by slug or name
    project = next(
        (
            p
            for p in projects
            if p.get("slug", "").lower() == slug.lower()
            or p.get("name", "").lower().replace(" ", "-") == slug.lower()
        ),
        None,
    )

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{slug}' not found.")

    return {
        "project": project,
        "ai_explanation_endpoint": f"/api/v1/chat (ask: 'Tell me about the {project['name']} project')",
    }


@router.get("/projects/{slug}/explain")
async def explain_project(slug: str, request: Request):
    """
    AI-generated deep explanation of a specific project.
    Triggers Repo Intelligence if GitHub URL is configured.
    """
    portfolio = request.app.state.portfolio
    projects = portfolio.get("projects", [])

    project = next(
        (
            p
            for p in projects
            if p.get("slug", "").lower() == slug.lower()
            or p.get("name", "").lower().replace(" ", "-") == slug.lower()
        ),
        None,
    )

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{slug}' not found.")

    rag = request.app.state.rag_engine
    query = f"Explain the {project['name']} project in detail — architecture, tech stack, challenges, and what makes it impressive."
    context_chunks = await rag.retrieve(query, mode="technical")
    system_prompt = _guard.build_system_prompt("technical")
    explanation = await complete_claude(system_prompt, query, context_chunks)

    return {
        "project_name": project["name"],
        "explanation": explanation,
        "tech_stack": project.get("tech_stack", []),
        "github_url": project.get("github_url", ""),
        "demo_url": project.get("demo_url", ""),
    }
