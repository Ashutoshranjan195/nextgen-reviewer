"""
Authentication routes — user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, MessageResponse, RegisterRequest, TokenResponse
from app.security import get_client_ip, is_ip_blocked, register_failed_attempt, clear_ip_attempts

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.

    - Validates that the username is not already taken.
    - Hashes the password with bcrypt.
    - Returns a success message.
    """
    # Check for existing user
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # Create user
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()

    return MessageResponse(message="User created")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate a user and return a JWT access token.
    """
    # 1. Get Real IP
    client_ip = get_client_ip(request)

    # 2. Strict Check: IP Blocked?
    if await is_ip_blocked(db, client_ip):
        raise HTTPException(
            status_code=403,
            detail=f"Too many failed attempts. IP blocked for 15 minutes."
        )

    # 3. Fetch User
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    # 4. Validate Password
    if not user or not verify_password(body.password, user.password_hash):
        # Register failure
        await register_failed_attempt(db, client_ip, body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # 3. Successful login - clear attempts
    await clear_ip_attempts(db, client_ip)

    token = create_access_token(data={"sub": user.username})

    return TokenResponse(access_token=token, username=user.username)
