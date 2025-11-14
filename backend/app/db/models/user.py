"""
User ORM model.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """User model for storing user account information."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    email = Column(String(255), nullable=True)
    total_generations = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationship
    generations = relationship("Generation", back_populates="user")

