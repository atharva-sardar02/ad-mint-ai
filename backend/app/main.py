"""
FastAPI application entry point.
"""
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, editor, generations, users
from app.core.config import settings
from app.core.logging import setup_logging

# Setup structured logging
setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ad Mint AI",
    description="AI Video Ad Generator API",
    version="0.1.0",
)

# CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers (after CORS middleware)
app.include_router(auth.router)
app.include_router(generations.router)
app.include_router(users.router)
app.include_router(editor.router)

# Mount static files for serving videos and thumbnails
# This allows the frontend to access files at /output/videos/ and /output/thumbnails/
output_dir = Path("output")
if output_dir.exists():
    app.mount("/output", StaticFiles(directory="output"), name="output")
    logger.info("Static files mounted at /output")
else:
    logger.warning("Output directory not found - static file serving disabled")


@app.on_event("startup")
async def startup_event():
    """Startup event."""
    logger.info("Ad Mint AI API started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Ad Mint AI API"}


@app.get("/api/health")
async def health():
    """
    Enhanced health check endpoint with component-level status.
    
    Returns:
        dict: Health status with database, storage, and external API checks
    """
    from app.core.config import settings
    from app.db.base import engine
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Database connectivity check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite",
            "connection": "vpc" if "postgresql" in settings.DATABASE_URL else "local"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # S3 storage check (if storage mode is S3)
    if settings.STORAGE_MODE == "s3":
        try:
            from app.services.storage.s3_storage import get_s3_storage
            s3_storage = get_s3_storage()
            if s3_storage.test_connection():
                health_status["components"]["storage"] = {
                    "status": "healthy",
                    "type": "s3",
                    "bucket": settings.AWS_S3_VIDEO_BUCKET
                }
            else:
                health_status["status"] = "degraded"
                health_status["components"]["storage"] = {
                    "status": "unhealthy",
                    "type": "s3",
                    "error": "S3 connection test failed"
                }
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["components"]["storage"] = {
                "status": "unhealthy",
                "type": "s3",
                "error": str(e)
            }
    else:
        health_status["components"]["storage"] = {
            "status": "healthy",
            "type": "local"
        }
    
    # External API checks (optional - don't fail health check if external APIs are down)
    external_apis = {}
    
    # Replicate API check (basic - just verify token is set)
    if settings.REPLICATE_API_TOKEN:
        external_apis["replicate"] = {
            "status": "configured",
            "token_set": True
        }
    else:
        external_apis["replicate"] = {
            "status": "not_configured",
            "token_set": False
        }
    
    # OpenAI API check (basic - just verify key is set)
    if settings.OPENAI_API_KEY:
        external_apis["openai"] = {
            "status": "configured",
            "key_set": True
        }
    else:
        external_apis["openai"] = {
            "status": "not_configured",
            "key_set": False
        }
    
    health_status["components"]["external_apis"] = external_apis
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return health_status

