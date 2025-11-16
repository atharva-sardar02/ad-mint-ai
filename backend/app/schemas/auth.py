"""
Pydantic schemas for authentication requests and responses.
"""
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class UserRegister(BaseModel):
    """Schema for user registration request."""

    username: str = Field(
        ..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$"
    )
    password: str = Field(..., min_length=8, max_length=100)
    email: Optional[str] = Field(None, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login request."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """Schema for user information in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: Optional[str] = None
    total_generations: int
    total_cost: float


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse

