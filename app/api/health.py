"""
app/api/health.py
──────────────────
Health check endpoints for load balancer + monitoring.
"""

from fastapi import APIRouter, Request
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness(request: Request):
    """Check if indexes are loaded and system is ready."""
    try:
        index_manager = request.app.state.index_manager
        portfolio_size = index_manager.portfolio_index.size
        resume_size = index_manager.resume_index.size
        return {
            "status": "ready",
            "indexes": {
                "portfolio_vectors": portfolio_size,
                "resume_vectors": resume_size,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
