"""
Product Image route handlers.
"""
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.product_image import ProductImageFolder
from app.db.models.uploaded_image import UploadedImage
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.product_image import (
    ProductImageListResponse,
    ProductImageUploadResponse,
)
from app.schemas.brand_style import UploadedImageResponse
from app.utils.storage import (
    MAX_IMAGES_PER_FOLDER,
    delete_user_folder,
    save_uploaded_images,
    validate_folder_size,
    validate_image_count,
    validate_image_file,
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("/upload", status_code=status.HTTP_200_OK, response_model=ProductImageUploadResponse)
async def upload_product_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductImageUploadResponse:
    """
    Upload product images for the current user.

    Args:
        files: List of uploaded image files (multipart/form-data)
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        ProductImageUploadResponse with success message and image count

    Raises:
        HTTPException: 400 if validation fails, 401 if not authenticated, 413 if too large, 500 if server error
    """
    try:
        logger.info(f"Upload request received from user {current_user.id} with {len(files) if files else 0} files")
        
        # Validate files are provided
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "NO_FILES",
                        "message": "No files provided",
                    }
                },
            )

        # Validate each file
        for file in files:
            if not validate_image_file(file):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": "INVALID_FILE_TYPE",
                            "message": f"File {file.filename} is not a valid image type (JPEG, PNG, WebP only)",
                        }
                    },
                )

        # Validate folder size
        if not await validate_folder_size(files, max_size_mb=100):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": "FOLDER_TOO_LARGE",
                        "message": f"Folder size exceeds maximum allowed size (100MB)",
                    }
                },
            )

        # Validate image count
        if not validate_image_count(files, max_count=MAX_IMAGES_PER_FOLDER):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "TOO_MANY_IMAGES",
                        "message": f"Maximum {MAX_IMAGES_PER_FOLDER} images allowed per folder",
                    }
                },
            )

        # Delete existing product folder if it exists (replacement behavior)
        existing_folder = db.query(ProductImageFolder).filter(ProductImageFolder.user_id == current_user.id).first()
        if existing_folder:
            # Delete all related uploaded images from database
            db.query(UploadedImage).filter(
                UploadedImage.folder_id == existing_folder.id,
                UploadedImage.folder_type == "product"
            ).delete()
            
            # Delete folder from database
            db.delete(existing_folder)
            db.commit()
            
            # Delete physical folder from disk
            try:
                delete_user_folder(current_user.id, "products")
            except Exception as e:
                logger.warning(f"Error deleting existing product folder: {e}")

        # Save uploaded images to disk
        saved_paths = await save_uploaded_images(current_user.id, files, "products")

        if not saved_paths:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "NO_VALID_FILES",
                        "message": "No valid image files were uploaded",
                    }
                },
            )

        # Create ProductImageFolder record
        product_image_folder = ProductImageFolder(
            user_id=current_user.id,
            image_count=len(saved_paths),
        )
        db.add(product_image_folder)
        db.flush()  # Flush to get folder ID

        # Create UploadedImage records for each saved file
        for saved_path in saved_paths:
            file_path = Path(saved_path)
            uploaded_image = UploadedImage(
                folder_id=product_image_folder.id,
                folder_type="product",
                filename=file_path.name,
                file_path=saved_path,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
            )
            db.add(uploaded_image)

        db.commit()
        db.refresh(product_image_folder)

        logger.info(f"Product images uploaded successfully for user {current_user.id}: {len(saved_paths)} images")

        return ProductImageUploadResponse(
            message=f"Product images uploaded successfully ({len(saved_paths)} images)",
            count=len(saved_paths),
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading product images: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "UPLOAD_FAILED",
                    "message": "Failed to upload product images",
                }
            },
        )


@router.get("", response_model=ProductImageListResponse)
async def get_product_images(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProductImageListResponse:
    """
    Get list of product images for the current user.

    Args:
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        ProductImageListResponse with list of uploaded images

    Raises:
        HTTPException: 401 if not authenticated, 500 if server error
    """
    try:
        # Query product image folder for user
        product_image_folder = db.query(ProductImageFolder).filter(ProductImageFolder.user_id == current_user.id).first()

        if not product_image_folder:
            return ProductImageListResponse(images=[])

        # Query uploaded images for this folder
        uploaded_images = db.query(UploadedImage).filter(
            UploadedImage.folder_id == product_image_folder.id,
            UploadedImage.folder_type == "product"
        ).all()

        # Build response with image URLs
        image_responses = []
        for image in uploaded_images:
            # Get the actual filename from the file_path (this is what was actually saved)
            # The file_path might be relative or absolute, so extract just the filename
            actual_filename = Path(image.file_path).name
            
            # Generate URL: /api/assets/users/{user_id}/products/{filename}
            # Use the actual saved filename to ensure the URL matches the file on disk
            image_url = f"/api/assets/users/{current_user.id}/products/{actual_filename}"
            
            logger.debug(f"Image URL: {image_url}, stored filename: {image.filename}, actual filename: {actual_filename}, file_path: {image.file_path}")
            
            image_responses.append(
                UploadedImageResponse(
                    id=image.id,
                    filename=actual_filename,  # Use actual filename that matches the saved file
                    url=image_url,
                    uploaded_at=image.uploaded_at,
                )
            )

        return ProductImageListResponse(images=image_responses)

    except Exception as e:
        logger.error(f"Error getting product images: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "GET_FAILED",
                    "message": "Failed to retrieve product images",
                }
            },
        )


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_product_images(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete all product images for the current user.

    Args:
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 401 if not authenticated, 500 if server error
    """
    try:
        # Query product image folder for user
        product_image_folder = db.query(ProductImageFolder).filter(ProductImageFolder.user_id == current_user.id).first()

        if not product_image_folder:
            return {"message": "No product images found to delete"}

        # Delete all related uploaded images from database
        db.query(UploadedImage).filter(
            UploadedImage.folder_id == product_image_folder.id,
            UploadedImage.folder_type == "product"
        ).delete()

        # Delete folder from database
        db.delete(product_image_folder)
        db.commit()

        # Delete physical folder from disk
        try:
            delete_user_folder(current_user.id, "products")
        except Exception as e:
            logger.warning(f"Error deleting product folder from disk: {e}")

        logger.info(f"Product images deleted successfully for user {current_user.id}")

        return {"message": "Product images deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting product images: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "DELETE_FAILED",
                    "message": "Failed to delete product images",
                }
            },
        )

