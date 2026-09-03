from datetime import datetime, timedelta
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from app.models import FailedLoginAttempt

MAX_FAILED_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 15

def get_client_ip(request: Request) -> str:
    """Extract real IP address from request, handling reverse proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

async def is_ip_blocked(db: AsyncSession, ip: str) -> bool:
    """Check if IP has exceeded max failed attempts in the time window."""
    time_limit = datetime.utcnow() - timedelta(minutes=BLOCK_DURATION_MINUTES)
    stmt = select(func.count(FailedLoginAttempt.id)).where(
        FailedLoginAttempt.ip_address == ip,
        FailedLoginAttempt.timestamp >= time_limit
    )
    result = await db.execute(stmt)
    count = result.scalar_one()
    return count >= MAX_FAILED_ATTEMPTS

async def register_failed_attempt(db: AsyncSession, ip: str, username: str = None):
    """Log a failed attempt and clean up records older than the block window."""
    # 1. Insert new failed attempt
    new_attempt = FailedLoginAttempt(ip_address=ip, username_attempted=username)
    db.add(new_attempt)
    
    # 2. Delete old attempts to keep database small
    time_limit = datetime.utcnow() - timedelta(minutes=BLOCK_DURATION_MINUTES)
    delete_stmt = delete(FailedLoginAttempt).where(FailedLoginAttempt.timestamp < time_limit)
    await db.execute(delete_stmt)
    
    await db.commit()

async def clear_ip_attempts(db: AsyncSession, ip: str):
    """Clear all failed attempts for an IP upon successful login."""
    stmt = delete(FailedLoginAttempt).where(FailedLoginAttempt.ip_address == ip)
    await db.execute(stmt)
    await db.commit()
