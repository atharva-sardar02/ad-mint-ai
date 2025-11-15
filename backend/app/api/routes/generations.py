"""
Generation route handlers for video gallery.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.generation import Generation
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.generation import GenerationListResponse, GenerationListItem

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generations", tags=["generations"])


@router.get("", response_model=GenerationListResponse)
async def get_generations(
    limit: int = Query(default=20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(
        default=None,
        description="Filter by status (pending, processing, completed, failed)",
    ),
    q: Optional[str] = Query(
        default=None, description="Search term for prompt text (case-insensitive)"
    ),
    sort: str = Query(
        default="created_at_desc",
        description="Sort order (created_at_desc, created_at_asc)",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerationListResponse:
    """
    Get paginated list of user's video generations.

    Args:
        limit: Number of results per page (1-100, default: 20)
        offset: Pagination offset (default: 0)
        status: Optional status filter (pending, processing, completed, failed)
        q: Optional search term for prompt text (case-insensitive substring match)
        sort: Sort order (created_at_desc or created_at_asc, default: created_at_desc)
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        GenerationListResponse with total, limit, offset, and generations array

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 422 if validation fails (handled by FastAPI)
    """
    # Build base query - filter by user_id
    query = db.query(Generation).filter(Generation.user_id == current_user.id)

    # Apply status filter if provided
    if status:
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_STATUS",
                        "message": f"Status must be one of: {', '.join(valid_statuses)}",
                    }
                },
            )
        query = query.filter(Generation.status == status)

    # Apply search filter if provided (case-insensitive substring match on prompt)
    if q:
        query = query.filter(Generation.prompt.ilike(f"%{q}%"))

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    if sort == "created_at_asc":
        query = query.order_by(Generation.created_at.asc())
    else:  # default to created_at_desc (newest first)
        query = query.order_by(Generation.created_at.desc())

    # Apply pagination
    generations = query.offset(offset).limit(limit).all()

    # Convert to Pydantic models
    generation_items = [
        GenerationListItem(
            id=gen.id,
            prompt=gen.prompt,
            status=gen.status,
            video_url=gen.video_url,
            thumbnail_url=gen.thumbnail_url,
            duration=gen.duration,
            cost=gen.cost,
            created_at=gen.created_at,
            completed_at=gen.completed_at,
        )
        for gen in generations
    ]

    logger.info(
        f"User {current_user.id} retrieved {len(generation_items)} generations "
        f"(total: {total}, offset: {offset}, limit: {limit})"
    )

    return GenerationListResponse(
        total=total,
        limit=limit,
        offset=offset,
        generations=generation_items,
    )

