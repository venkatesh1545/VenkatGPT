# VenkatGPT — AI-Powered Personal Identity Engine

> Your professional AI replica. Built on RAG. Powered by Claude. Zero hallucinations.

---

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/venkatgpt
cd venkatgpt

# Copy environment variables
cp .env.example .env
# → Open .env and fill in your ANTHROPIC_API_KEY (required) and GITHUB_TOKEN (optional)
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Fill Your Data

Edit `data/portfolio.json` — replace ALL of Venkat's data with YOUR data:
- Your name, summary, contact info
- Your projects (with GitHub URLs)
- Your skills, certifications, achievements
- Your experience and education

Optionally place your resume at `data/resume.pdf`

### 4. Build Indexes

```bash
python scripts/build_index.py
```

This creates FAISS indexes in `indexes/` from your portfolio.json and resume.pdf.
Run this every time you update your portfolio data.

### 5. Start Backend

```bash
uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs — Swagger UI with all endpoints

### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000 — Chat UI

---

## Project Structure

```
venkatgpt/
├── app/
│   ├── main.py                    ← FastAPI app (START HERE)
│   ├── config.py                  ← All settings
│   ├── api/
│   │   ├── chat.py                ← POST /api/v1/chat (streaming)
│   │   ├── projects.py            ← GET /api/v1/projects
│   │   ├── resume.py              ← GET /api/v1/resume/*
│   │   └── health.py              ← GET /health
│   ├── core/
│   │   ├── rag_engine.py          ← RAG orchestrator
│   │   ├── claude_client.py       ← Claude streaming API
│   │   └── persona_guard.py       ← Prompt builder + off-topic filter
│   ├── ingestion/
│   │   ├── portfolio_loader.py    ← JSON → chunks
│   │   ├── resume_loader.py       ← PDF → chunks
│   │   ├── github_fetcher.py      ← GitHub API → chunks
│   │   ├── chunker.py             ← Smart text splitting
│   │   └── embedder.py            ← SentenceTransformers
│   ├── vectorstore/
│   │   ├── faiss_store.py         ← FAISS index wrapper
│   │   └── index_manager.py       ← Manages all indexes
│   └── security/
│       ├── sanitizer.py           ← Prompt injection defense
│       └── rate_limiter.py        ← Redis rate limiting
├── data/
│   ├── portfolio.json             ← ⭐ YOUR DATA GOES HERE
│   └── resume.pdf                 ← Your resume (optional)
├── indexes/                       ← Auto-generated FAISS indexes
├── prompts/                       ← Editable persona prompts
│   ├── system_base.txt            ← Core persona
│   ├── hr_mode.txt                ← HR mode overlay
│   ├── technical_mode.txt         ← Technical mode overlay
│   └── summary_mode.txt           ← Summary mode overlay
├── scripts/
│   ├── build_index.py             ← Run after updating portfolio
│   └── refresh_portfolio.py       ← Rebuild + optional S3/ECS deploy
├── tests/                         ← pytest tests
├── docker/                        ← Docker + docker-compose
├── frontend/                      ← React chat UI
└── requirements.txt
```

---

## API Reference

### POST /api/v1/chat (Streaming)

```bash
curl -N -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about yourself", "mode": "hr"}'
```

Modes: `hr` | `technical` | `summary`

Response: Server-Sent Events stream
```
data: {"type": "token", "data": "I'm "}
data: {"type": "token", "data": "Venkat..."}
data: {"type": "done", "data": ""}
```

### POST /api/v1/chat/sync (Non-streaming)

```bash
curl -X POST http://localhost:8000/api/v1/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"query": "What is your tech stack?", "mode": "technical"}'
```

### GET /api/v1/projects
### GET /api/v1/projects/{slug}
### GET /api/v1/resume/summary
### GET /api/v1/resume/download
### GET /health | /ready

---

## Customization

### Change the AI's Persona

Edit `prompts/system_base.txt` — this controls tone, identity rules, and the Unknown Question Protocol.

### Add a New Mode

1. Create `prompts/yourmode.txt`
2. Add it to `app/core/persona_guard.py` in `self.mode_prompts`
3. Add to `ChatMode` enum in `app/models/chat.py`

### Update Your Portfolio

1. Edit `data/portfolio.json`
2. Run: `python scripts/build_index.py`
3. Restart server (or it auto-rebuilds on first missing index)

---

## Docker

```bash
cd docker
docker-compose up --build
```

Backend: http://localhost:8000
Redis: localhost:6379

---

## Tests

```bash
pytest tests/ -v
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Get from console.anthropic.com |
| `GITHUB_TOKEN` | Optional | For Repo Intelligence (private repos need this) |
| `GITHUB_USERNAME` | Optional | Your GitHub username |
| `REDIS_URL` | Optional | Enables rate limiting. Default: `redis://localhost:6379` |
| `RESUME_DOWNLOAD_URL` | Optional | Public URL to your resume PDF |
| `RESUME_VIEW_URL` | Optional | Public URL to view resume |
| `SECRET_KEY` | Recommended | JWT secret (use a long random string) |

---

## How It Works

```
User Question
    │
    ▼
Security Layer (sanitize + rate limit + off-topic filter)
    │
    ▼
Query Embedding (SentenceTransformers all-MiniLM-L6-v2)
    │
    ▼
FAISS Similarity Search → Top-K chunks from portfolio + resume
    │
    ▼ (if project name detected in query)
GitHub Repo Intelligence → fetch README + code → dynamic FAISS index
    │
    ▼
Context Assembly → deduplicate + rank + cap at token limit
    │
    ▼
Persona Guard → build system prompt (base + mode overlay)
    │
    ▼
Claude claude-sonnet-4-6 → stream response → SSE to client
```

---

Built with ❤️ by Venkat
