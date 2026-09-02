"""
Review routes — code submission and history retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Rule, Submission, User
from app.reviewer import generate_review
from app.schemas import (
    HistoryResponse,
    ReviewResponse,
    SubmissionSummary,
    SubmitRequest,
    Issue,
)

router = APIRouter(prefix="/api", tags=["review"])

# Supported languages
SUPPORTED_LANGUAGES = {
    "python", "javascript", "typescript", "java", "go",
    "rust", "c++", "c#", "ruby", "php",
    "c", "swift", "kotlin", "scala", "html", "css", "sql",
}


def _code_preview(code: str, max_length: int = 200) -> str:
    """Generate a truncated code preview."""
    preview = code.strip()
    if len(preview) > max_length:
        preview = preview[:max_length] + "..."
    return preview


@router.post("/submit", response_model=ReviewResponse)
async def submit_code(
    body: SubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit code for AI-powered review.

    1. Validates code length and language.
    2. Fetches the user's + global historical rules.
    3. Calls the LLM review engine.
    4. Saves the submission to the database.
    5. Returns the structured review.
    """
    # ── Validate code length ──────────────────────────────────────────────
    if len(body.code) > settings.MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code exceeds maximum length of {settings.MAX_CODE_LENGTH:,} characters",
        )

    if not body.code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code cannot be empty",
        )

    # Normalize language
    language = body.language.strip().lower()

    # ── Fetch historical rules (user-specific + global) ───────────────────
    rules_result = await db.execute(
        select(Rule).where(
            (Rule.user_id == user.id) | (Rule.user_id.is_(None))
        )
    )
    rules = [
        {"type": r.type, "description": r.description}
        for r in rules_result.scalars().all()
    ]

    # ── Generate review via LLM ───────────────────────────────────────────
    review = await generate_review(
        code=body.code,
        language=language,
        rules=rules,
    )

    # ── Persist submission ────────────────────────────────────────────────
    submission = Submission(
        user_id=user.id,
        code=body.code,
        language=language,
        rating=review.rating,
        feedback=review.feedback,
        issues=[{"type": i["type"], "description": i["description"]} for i in review.issues],
    )
    db.add(submission)
    await db.flush()

    # ── Return response ──────────────────────────────────────────────────
    return ReviewResponse(
        rating=review.rating,
        feedback=review.feedback,
        issues=[Issue(type=i["type"], description=i["description"]) for i in review.issues],
        language=language,
        code_preview=_code_preview(body.code),
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all code review submissions for the authenticated user,
    sorted by creation date (oldest first).
    """
    result = await db.execute(
        select(Submission)
        .where(Submission.user_id == user.id)
        .order_by(Submission.created_at.asc())
    )
    submissions = result.scalars().all()

    return HistoryResponse(
        submissions=[
            SubmissionSummary(
                id=s.id,
                code_preview=_code_preview(s.code),
                language=s.language,
                rating=s.rating,
                created_at=s.created_at.isoformat() if s.created_at else "",
            )
            for s in submissions
        ]
    )
