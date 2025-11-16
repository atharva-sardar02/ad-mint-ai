"""
Pydantic schemas for user-related requests and responses.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """Schema for user profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: Optional[str] = None
    total_generations: int
    total_cost: float
    created_at: datetime
    last_login: Optional[datetime] = None

