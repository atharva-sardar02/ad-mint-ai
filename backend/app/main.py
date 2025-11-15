"""
FastAPI application entry point.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, generations
from app.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ad Mint AI",
    description="AI Video Ad Generator API",
    version="0.1.0",
)

# Include routers
app.include_router(auth.router)
app.include_router(generations.router)

# CORS middleware configuration
# Note: CORS middleware should handle preflight OPTIONS requests automatically
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods for development
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers to the frontend
)


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

