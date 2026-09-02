"""
ORM models — User, Submission, Rule.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """Registered user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    rules = relationship("Rule", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r}>"


class Submission(Base):
    """A single code review submission."""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    rating = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=False)
    issues = Column(JSON, default=list)  # List of {"type": str, "description": str}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="submissions")

    def __repr__(self):
        return f"<Submission id={self.id} lang={self.language!r} rating={self.rating}>"


class Rule(Base):
    """Historical rule imported from CSV."""
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL = global rule
    type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="rules")

    def __repr__(self):
        return f"<Rule id={self.id} type={self.type!r}>"
