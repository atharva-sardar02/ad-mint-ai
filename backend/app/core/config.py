"""
Environment variable management and configuration.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Get the backend directory (where this file is located)
BACKEND_DIR = Path(__file__).parent.parent.parent

# Load environment variables from .env file in backend directory
env_path = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./ad_mint_ai.db"
    )

    # API configuration
    API_V1_PREFIX: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")  # 7 days default
    )

    # External API keys (placeholders for now)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    REPLICATE_API_TOKEN: Optional[str] = os.getenv("REPLICATE_API_TOKEN")

    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    PROJECT_NAME: str = "Ad Mint AI"

    # CORS configuration
    CORS_ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
        ).split(",")
    ]

    # Static file serving configuration
    STATIC_BASE_URL: str = os.getenv(
        "STATIC_BASE_URL", "http://localhost:8000/output"
    )

    # Output directory for generated files
    OUTPUT_BASE_DIR: str = os.getenv(
        "OUTPUT_BASE_DIR", str(BACKEND_DIR / "cli_tools" / "output")
    )
    # AWS S3 configuration
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_VIDEO_BUCKET: str = os.getenv("AWS_S3_VIDEO_BUCKET", "ad-mint-ai-videos")
    
    # Storage mode: 'local' for local disk, 's3' for S3 storage
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "local")
    
    # Quality control thresholds (VBench metrics)
    QUALITY_THRESHOLD_TEMPORAL: float = float(os.getenv("QUALITY_THRESHOLD_TEMPORAL", "70.0"))
    QUALITY_THRESHOLD_FRAME_WISE: float = float(os.getenv("QUALITY_THRESHOLD_FRAME_WISE", "70.0"))
    QUALITY_THRESHOLD_TEXT_VIDEO_ALIGNMENT: float = float(os.getenv("QUALITY_THRESHOLD_TEXT_VIDEO_ALIGNMENT", "70.0"))
    QUALITY_THRESHOLD_OVERALL: float = float(os.getenv("QUALITY_THRESHOLD_OVERALL", "70.0"))
    
    # Automatic regeneration based on quality scores (disabled by default)
    # When False: Quality is evaluated and stored, but regeneration is not triggered automatically
    # Quality metrics are still available via API for manual review
    ENABLE_AUTOMATIC_REGENERATION: bool = os.getenv("ENABLE_AUTOMATIC_REGENERATION", "false").lower() == "true"

    # Redis configuration (for session storage)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")  # e.g., "redis://localhost:6379/0"

settings = Settings()

