"""
Storage utilities for managing user-uploaded brand style and product images.
"""
import logging
import shutil
from pathlib import Path
from typing import List

from fastapi import UploadFile
from app.core.config import BACKEND_DIR

# Set up logging
logger = logging.getLogger(__name__)

# Storage base directory - relative to backend directory
STORAGE_BASE_DIR = BACKEND_DIR / "assets" / "users"

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

# Allowed image file extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Maximum folder size (100MB in bytes)
MAX_FOLDER_SIZE_BYTES = 100 * 1024 * 1024  # 100MB

# Maximum number of images per folder
MAX_IMAGES_PER_FOLDER = 50


def ensure_user_directory(user_id: str, folder_type: str) -> Path:
    """
    Ensure user directory exists for the specified folder type.
    
    Args:
        user_id: User ID
        folder_type: Type of folder ('brand_styles' or 'products')
    
    Returns:
        Path to the user's folder directory
    
    Raises:
        OSError: If directory creation fails
    """
    if folder_type not in ("brand_styles", "products"):
        raise ValueError(f"Invalid folder_type: {folder_type}. Must be 'brand_styles' or 'products'")
    
    user_dir = STORAGE_BASE_DIR / user_id / folder_type
    user_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Ensured directory exists: {user_dir}")
    return user_dir


def validate_image_file(file: UploadFile) -> bool:
    """
    Validate that the uploaded file is an allowed image type.
    
    Args:
        file: Uploaded file
    
    Returns:
        True if file is valid, False otherwise
    """
    # Check MIME type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        logger.warning(f"Invalid content type: {file.content_type}")
        return False
    
    # Check file extension
    filename = file.filename or ""
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        logger.warning(f"Invalid file extension: {file_ext}")
        return False
    
    return True


async def validate_folder_size(files: List[UploadFile], max_size_mb: int = 100) -> bool:
    """
    Validate that the total size of all files doesn't exceed the maximum.
    
    Note: This reads all file contents into memory to check sizes.
    For large folders, consider streaming or checking file sizes from metadata.
    
    Args:
        files: List of uploaded files
        max_size_mb: Maximum folder size in MB (default: 100)
    
    Returns:
        True if folder size is valid, False otherwise
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    total_size = 0
    
    for file in files:
        # Note: This requires reading file contents which may be memory-intensive
        # In production, consider checking Content-Length header or streaming
        try:
            # Read file to get size (this moves file pointer to end)
            content = await file.read()
            file_size = len(content)
            total_size += file_size
            
            # Reset file pointer for later use (UploadFile.file is the underlying file object)
            file.file.seek(0)
        except Exception as e:
            logger.error(f"Error reading file {file.filename}: {e}")
            return False
        
        if total_size > max_size_bytes:
            logger.warning(f"Folder size exceeds maximum: {total_size} bytes > {max_size_bytes} bytes")
            return False
    
    return True


def validate_image_count(files: List[UploadFile], max_count: int = 50) -> bool:
    """
    Validate that the number of files doesn't exceed the maximum.
    
    Args:
        files: List of uploaded files
        max_count: Maximum number of images (default: 50)
    
    Returns:
        True if image count is valid, False otherwise
    """
    if len(files) > max_count:
        logger.warning(f"Too many images: {len(files)} > {max_count}")
        return False
    
    return True


async def save_uploaded_images(user_id: str, files: List[UploadFile], folder_type: str) -> List[str]:
    """
    Save uploaded images to user's directory.
    
    Args:
        user_id: User ID
        files: List of uploaded files
        folder_type: Type of folder ('brand_styles' or 'products')
    
    Returns:
        List of saved file paths (relative to project root)
    
    Raises:
        OSError: If file saving fails
        ValueError: If folder_type is invalid
    """
    if folder_type not in ("brand_styles", "products"):
        raise ValueError(f"Invalid folder_type: {folder_type}. Must be 'brand_styles' or 'products'")
    
    # Ensure directory exists
    user_dir = ensure_user_directory(user_id, folder_type)
    
    saved_paths = []
    
    for file in files:
        # Validate file
        if not validate_image_file(file):
            logger.warning(f"Skipping invalid file: {file.filename}")
            continue
        
        # Sanitize filename (preserve original but remove special characters that could cause issues)
        # When using webkitdirectory, filenames may include path separators - extract just the filename
        filename = file.filename or "image"
        # Extract just the filename (remove any path components from webkitdirectory)
        filename = Path(filename).name
        # Replace potentially dangerous characters but preserve valid characters
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (".", "-", "_")).strip()
        
        # Ensure filename has extension
        if not Path(safe_filename).suffix:
            # Add extension based on content type
            if file.content_type == "image/webp":
                safe_filename += ".webp"
            elif file.content_type in ("image/jpeg", "image/jpg"):
                safe_filename += ".jpg"
            elif file.content_type == "image/png":
                safe_filename += ".png"
        
        # Handle duplicate filenames by appending number
        file_path = user_dir / safe_filename
        counter = 1
        while file_path.exists():
            stem = Path(safe_filename).stem
            suffix = Path(safe_filename).suffix
            safe_filename = f"{stem}_{counter}{suffix}"
            file_path = user_dir / safe_filename
            counter += 1
        
        # Read file contents
        content = await file.read()
        
        # Save file
        file_path.write_bytes(content)
        
        # Store path relative to BACKEND_DIR for consistency
        # This ensures the path works regardless of where the app is run from
        try:
            relative_path = str(file_path.relative_to(BACKEND_DIR))
        except ValueError:
            # If not relative to BACKEND_DIR, use absolute path as fallback
            relative_path = str(file_path.absolute())
        saved_paths.append(relative_path)
        
        logger.info(f"Saved image: {relative_path} (absolute: {file_path.absolute()})")
    
    return saved_paths


def delete_user_folder(user_id: str, folder_type: str) -> None:
    """
    Delete user's folder and all its contents.
    
    Args:
        user_id: User ID
        folder_type: Type of folder ('brand_styles' or 'products')
    
    Raises:
        OSError: If folder deletion fails
        ValueError: If folder_type is invalid
    """
    if folder_type not in ("brand_styles", "products"):
        raise ValueError(f"Invalid folder_type: {folder_type}. Must be 'brand_styles' or 'products'")
    
    user_dir = STORAGE_BASE_DIR / user_id / folder_type
    
    if user_dir.exists() and user_dir.is_dir():
        shutil.rmtree(user_dir)
        logger.info(f"Deleted folder: {user_dir}")
    else:
        logger.info(f"Folder does not exist, skipping deletion: {user_dir}")


def get_user_folder_path(user_id: str, folder_type: str) -> Path:
    """
    Get the path to user's folder directory (does not create it).
    
    Args:
        user_id: User ID
        folder_type: Type of folder ('brand_styles' or 'products')
    
    Returns:
        Path to the user's folder directory
    """
    if folder_type not in ("brand_styles", "products"):
        raise ValueError(f"Invalid folder_type: {folder_type}. Must be 'brand_styles' or 'products'")
    
    return STORAGE_BASE_DIR / user_id / folder_type

