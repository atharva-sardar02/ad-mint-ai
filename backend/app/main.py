"""
FastAPI application entry point.
"""
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import auth, editor, generations, generations_with_image, users
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

# CORS middleware - allow frontend origins
# Note: Cannot use allow_origins=["*"] with allow_credentials=True
# Must explicitly list allowed origins
# IMPORTANT: CORS middleware must be added BEFORE exception handlers
logger.info(f"CORS allowed origins: {settings.CORS_ALLOWED_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Helper function to get CORS headers
def get_cors_headers(request: Request) -> dict:
    """
    Get CORS headers for a request, respecting allowed origins.
    """
    origin = request.headers.get("origin")
    if origin and origin in settings.CORS_ALLOWED_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    # If origin not in allowed list, don't add CORS headers (CORS middleware will handle it)
    return {}

# Global exception handler to ensure CORS headers are added to error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure CORS headers are added to all error responses.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return error response with CORS headers
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred"
            }
        },
        headers=get_cors_headers(request)
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HTTP exception handler to ensure CORS headers are added.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"detail": str(exc.detail)},
        headers=get_cors_headers(request)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Validation exception handler to ensure CORS headers are added.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors()
            }
        },
        headers=get_cors_headers(request)
    )

# Include routers (after CORS middleware)
app.include_router(auth.router)
app.include_router(generations.router)
app.include_router(generations_with_image.router)
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

