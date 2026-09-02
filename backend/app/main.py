"""
NextGen Code Reviewer — Main FastAPI Application

A 24/7 intelligent code review system with:
- JWT-based authentication
- Multi-language code review via rule-based analysis
- Historical rule learning from CSV uploads
- Persistent user submission history
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes.auth_routes import router as auth_router
from app.routes.review_routes import router as review_router
from app.routes.rules_routes import router as rules_router

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    logger.info("🚀 Starting NextGen Code Reviewer...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    logger.info("🛑 Shutting down NextGen Code Reviewer")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="NextGen Code Reviewer",
    description="24/7 Intelligent Code Review API with rule-based analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(review_router)
app.include_router(rules_router)


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["system"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "nextgen-code-reviewer"}


# ── Static Files (Frontend) ──────────────────────────────────────────────────
# NOTE: This must be LAST — the "/" mount is a catch-all that would shadow
# any routes defined after it.

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    logger.info("📁 Serving frontend from %s", frontend_dir)
