"""
Pydantic schemas — request and response models for the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    username: str


class MessageResponse(BaseModel):
    message: str


# ── Review ────────────────────────────────────────────────────────────────────

class SubmitRequest(BaseModel):
    code: str
    language: str


class Issue(BaseModel):
    type: str  # formatting | performance | security | best-practice | optimization | other
    description: str


class ReviewResponse(BaseModel):
    rating: int
    feedback: str
    issues: List[Issue]
    language: str
    code_preview: str


# ── History ───────────────────────────────────────────────────────────────────

class SubmissionSummary(BaseModel):
    id: int
    code_preview: str
    language: str
    rating: int
    created_at: str  # ISO format string


class HistoryResponse(BaseModel):
    submissions: List[SubmissionSummary]


# ── Rules ─────────────────────────────────────────────────────────────────────

class RuleOut(BaseModel):
    id: int
    type: str
    description: str


class RulesResponse(BaseModel):
    rules: List[RuleOut]
    count: int


class UploadResponse(BaseModel):
    count: int
    message: str
