"""
Structured logging configuration for FastAPI application.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.core.config import settings


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO"):
    """
    Configure structured logging for the application.
    
    Args:
        log_file: Path to log file (default: logs/app.log in project root, stdout in development if DEBUG=True)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Determine log file path
    # ALWAYS log to file (both DEBUG and production) so we can capture Sora prompts and LLM responses
    if log_file is None:
        # Use project-relative logs directory (preferred for development and production)
        # Get project root: backend/app/core -> backend/app -> backend -> project root
        project_root = Path(__file__).parent.parent.parent.parent
        project_log_dir = project_root / "logs"
        
        try:
            project_log_dir.mkdir(parents=True, exist_ok=True)
            log_file = str(project_log_dir / "app.log")
        except (PermissionError, OSError):
            # If project logs directory fails, try system log directory (production only)
            try:
                system_log_dir = Path("/var/log/fastapi")
                system_log_dir.mkdir(parents=True, exist_ok=True)
                log_file = str(system_log_dir / "app.log")
            except (PermissionError, OSError):
                # If both fail, just log to stdout
                # Note: Can't use logging.warning here as logger isn't configured yet
                print("WARNING: Could not create log directory. Logging to stdout only.")
                log_file = None
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter for structured logging
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (ALWAYS enabled to capture Sora prompts and LLM responses)
    if log_file:
        # Create rotating file handler
        # Max file size: 10MB, keep 5 backup files
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        logging.info(f"Logging to file: {log_file}")
    
    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

