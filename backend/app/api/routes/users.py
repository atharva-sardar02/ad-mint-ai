"""
User route handlers.
"""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.user import UserProfile

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfile:
    """
    Get current authenticated user's profile and statistics.

    Args:
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        UserProfile with user information and statistics

    Raises:
        HTTPException: 401 if not authenticated (handled by get_current_user dependency)
    """
    # Use Pydantic's model_validate for automatic serialization
    return UserProfile.model_validate(current_user)

