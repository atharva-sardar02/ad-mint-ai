"""
Authentication route handlers.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister, db: Session = Depends(get_db)
) -> dict:
    """
    Register a new user account.

    Args:
        user_data: User registration data (username, password, optional email)
        db: Database session

    Returns:
        Dictionary with success message and user_id

    Raises:
        HTTPException: 400 if username already exists
        HTTPException: 422 if validation fails (handled by FastAPI)
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing username: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "USERNAME_EXISTS",
                    "message": "Username already exists",
                }
            },
        )

    # Hash password with bcrypt (cost factor 12)
    hashed_password = hash_password(user_data.password)

    # Create new user
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        email=user_data.email,
        total_generations=0,
        total_cost=0.0,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully: {new_user.username} (id: {new_user.id})")
    except IntegrityError:
        db.rollback()
        logger.warning(f"Registration failed due to integrity error: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "USERNAME_EXISTS",
                    "message": "Username already exists",
                }
            },
        )

    return {
        "message": "User created successfully",
        "user_id": new_user.id,
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin, db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    Args:
        credentials: User login credentials (username, password)
        db: Database session

    Returns:
        TokenResponse with JWT token and user information

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Query user by username
    user = db.query(User).filter(User.username == credentials.username).first()

    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid username or password",
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    # Create JWT token
    token_data = {
        "sub": user.id,  # Subject (user ID) - standard JWT claim
        "username": user.username,
    }
    access_token = create_access_token(data=token_data)

    logger.info(f"User logged in successfully: {user.username} (id: {user.id})")

    # Return token and user information
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            total_generations=user.total_generations,
            total_cost=user.total_cost,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user (from dependency)

    Returns:
        UserResponse with user information
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        total_generations=current_user.total_generations,
        total_cost=current_user.total_cost,
    )

