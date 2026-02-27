"""
app/main.py
────────────
VenkatGPT — FastAPI Application Entry Point

Startup sequence:
1. Load portfolio.json
2. Load FAISS indexes (build if missing)
3. Initialize RAG engine
4. Mount all routers

Run locally:
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.api import chat, resume, projects, health
from app.vectorstore.index_manager import IndexManager
from app.ingestion.portfolio_loader import PortfolioLoader
from app.ingestion.resume_loader import ResumeLoader
from app.core.rag_engine import RAGEngine
from app.utils.logger import setup_logging

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""

    logger.info("═══ VenkatGPT Starting ═══")

    # ── Load Portfolio ─────────────────────────────────────────────────
    logger.info("Loading portfolio.json...")
    portfolio_loader = PortfolioLoader()
    portfolio = portfolio_loader.load(settings.PORTFOLIO_JSON_PATH)
    app.state.portfolio = portfolio
    logger.info(f"Portfolio loaded: {len(portfolio.get('projects', []))} projects, "
                f"{len(portfolio.get('certifications', []))} certs")

    # ── Load / Build Indexes ───────────────────────────────────────────
    logger.info("Loading FAISS indexes...")
    index_manager = IndexManager()

    # Check if portfolio index exists; build if not
    import os
    portfolio_index_path = os.path.join(settings.INDEXES_DIR, "portfolio", "index.faiss")
    if not os.path.exists(portfolio_index_path):
        logger.info("Portfolio index not found — building now (first run)...")
        portfolio_chunks = portfolio_loader.build_chunks(portfolio)
        index_manager.build_portfolio_index(portfolio_chunks)

        resume_loader = ResumeLoader()
        resume_chunks = resume_loader.load_and_chunk(settings.RESUME_PDF_PATH)
        index_manager.build_resume_index(resume_chunks)
        logger.info("Indexes built successfully.")
    else:
        index_manager.load_all()

    app.state.index_manager = index_manager

    # ── Initialize RAG Engine ──────────────────────────────────────────
    app.state.rag_engine = RAGEngine(index_manager, portfolio)
    logger.info("RAG engine initialized.")

    logger.info("═══ VenkatGPT Ready ═══")
    logger.info(f"Portfolio vectors: {index_manager.portfolio_index.size}")
    logger.info(f"Resume vectors:    {index_manager.resume_index.size}")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────
    logger.info("VenkatGPT shutting down...")


# ── Create App ─────────────────────────────────────────────────────────
app = FastAPI(
    title="VenkatGPT API",
    description="AI-powered personal identity engine — the AI version of Venkat",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

# ── Routers ────────────────────────────────────────────────────────────
app.include_router(chat.router,     prefix="/api/v1", tags=["Chat"])
app.include_router(resume.router,   prefix="/api/v1", tags=["Resume"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(health.router,                      tags=["Health"])


# ── Root ───────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": "VenkatGPT API",
        "version": "1.0.0",
        "message": "AI-powered professional replica of Venkat. Try POST /api/v1/chat",
        "docs": "/docs",
        "endpoints": {
            "chat_stream": "POST /api/v1/chat",
            "chat_sync": "POST /api/v1/chat/sync",
            "projects": "GET /api/v1/projects",
            "resume_summary": "GET /api/v1/resume/summary",
            "resume_download": "GET /api/v1/resume/download",
            "health": "GET /health",
        },
    }
