"""
FastAPI application entry point.
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, generations, users
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ad Mint AI",
    description="AI Video Ad Generator API",
    version="0.1.0",
)

# CORS middleware configuration
# IMPORTANT: CORS middleware must be added BEFORE routers to ensure it processes all requests
# Note: CORS middleware handles preflight OPTIONS requests automatically
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods for development
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers to the frontend
)

# Include routers (after CORS middleware)
app.include_router(auth.router)
app.include_router(generations.router)
app.include_router(users.router)

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
    """Log CORS configuration on startup."""
    logger.info(f"CORS allowed origins: {settings.CORS_ALLOWED_ORIGINS}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Ad Mint AI API"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

