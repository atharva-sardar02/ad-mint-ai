"""
Pydantic schemas for user-related requests and responses.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    """Schema for user profile response."""

    id: str
    username: str
    email: Optional[str]
    total_generations: int
    total_cost: float
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

