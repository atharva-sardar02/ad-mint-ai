"""
Pydantic schemas for authentication requests and responses.
"""
from typing import Optional

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Schema for user registration request."""

    username: str = Field(
        ..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_]+$"
    )
    password: str = Field(..., min_length=8, max_length=100)
    email: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login request."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """Schema for user information in responses."""

    id: str
    username: str
    email: Optional[str]
    total_generations: int
    total_cost: float

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse

