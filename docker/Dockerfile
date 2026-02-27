# ─────────────────────────────────────────────
# VenkatGPT — Production Dockerfile
# ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System dependencies for FAISS + PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p indexes/github_cache data

# Pre-build indexes if portfolio.json and resume.pdf exist
RUN if [ -f "data/portfolio.json" ]; then python scripts/build_index.py; fi

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop", "--access-log"]
