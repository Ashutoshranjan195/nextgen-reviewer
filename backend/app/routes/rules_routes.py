"""
Rules routes — CSV upload and rules retrieval.
"""

import csv
import io
import logging
import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Rule, User
from app.schemas import RuleOut, RulesResponse, UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["rules"])

# Required CSV columns
REQUIRED_COLUMNS = {"id", "type", "description"}


def parse_csv_sync(text: str):
    """Synchronous CPU-bound CSV parsing to be run in a thread pool."""
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV file is empty or has no headers")

    actual_columns = {col.strip().lower() for col in reader.fieldnames}
    missing = REQUIRED_COLUMNS - actual_columns
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    # Return a list of parsed rows so we don't keep the file object open across threads
    return list(reader)


@router.post("/upload-csv", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV file containing historical review rules.
    """
    if file.content_type and "csv" not in file.content_type and "text" not in file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV",
        )

    try:
        raw = await file.read()
        text = raw.decode("utf-8-sig") 
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )

    # Offload the blocking CSV parsing to a thread pool
    try:
        parsed_rows = await asyncio.to_thread(parse_csv_sync, text)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    imported = 0
    skipped = 0

    for row_num, row in enumerate(parsed_rows, start=2):
        normalized = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
        rule_type = normalized.get("type", "").strip()
        description = normalized.get("description", "").strip()

        if not rule_type or not description:
            skipped += 1
            logger.debug("Skipping row %d: missing type or description", row_num)
            continue

        rule = Rule(user_id=user.id, type=rule_type, description=description)
        db.add(rule)
        imported += 1

    if skipped > 0:
        logger.info("Skipped %d invalid rows during CSV import", skipped)

    await db.flush()

    return UploadResponse(
        count=imported,
        message=f"Imported {imported} rules" + (f" ({skipped} rows skipped)" if skipped else ""),
    )


@router.get("/rules", response_model=RulesResponse)
async def get_rules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all review rules available to the user.
    """
    result = await db.execute(
        select(Rule)
        .where((Rule.user_id == user.id) | (Rule.user_id.is_(None)))
        .order_by(Rule.created_at.asc())
    )
    rules = result.scalars().all()

    return RulesResponse(
        rules=[RuleOut(id=r.id, type=r.type, description=r.description) for r in rules],
        count=len(rules),
    )
