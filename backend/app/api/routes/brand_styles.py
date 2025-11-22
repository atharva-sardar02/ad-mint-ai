"""
Brand Style route handlers.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.brand_style import BrandStyleFolder
from app.db.models.uploaded_image import UploadedImage
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.brand_style import (
    BrandStyleExtractResponse,
    BrandStyleListResponse,
    BrandStyleUploadResponse,
    UploadedImageResponse,
)
from app.services.pipeline.brand_style_extractor import extract_brand_style, VISION_MODEL_COST_PER_IMAGE
from app.services.cost_tracking import track_vision_llm_cost
from app.db.models.brand_style import ExtractionStatus
from app.utils.storage import (
    MAX_FOLDER_SIZE_BYTES,
    MAX_IMAGES_PER_FOLDER,
    delete_user_folder,
    save_uploaded_images,
    validate_folder_size,
    validate_image_count,
    validate_image_file,
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brand-styles", tags=["brand-styles"])


@router.post("/upload", status_code=status.HTTP_200_OK, response_model=BrandStyleUploadResponse)
async def upload_brand_styles(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrandStyleUploadResponse:
    """
    Upload brand style images for the current user.

    Args:
        files: List of uploaded image files (multipart/form-data)
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        BrandStyleUploadResponse with success message and image count

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

        # Delete existing brand style folder if it exists (replacement behavior)
        existing_folder = db.query(BrandStyleFolder).filter(BrandStyleFolder.user_id == current_user.id).first()
        if existing_folder:
            # Delete all related uploaded images from database
            db.query(UploadedImage).filter(
                UploadedImage.folder_id == existing_folder.id,
                UploadedImage.folder_type == "brand_style"
            ).delete()
            
            # Delete folder from database
            db.delete(existing_folder)
            db.commit()
            
            # Delete physical folder from disk
            try:
                delete_user_folder(current_user.id, "brand_styles")
            except Exception as e:
                logger.warning(f"Error deleting existing brand style folder: {e}")

        # Save uploaded images to disk
        saved_paths = await save_uploaded_images(current_user.id, files, "brand_styles")

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

        # Create BrandStyleFolder record
        brand_style_folder = BrandStyleFolder(
            user_id=current_user.id,
            image_count=len(saved_paths),
        )
        db.add(brand_style_folder)
        db.flush()  # Flush to get folder ID

        # Create UploadedImage records for each saved file
        for saved_path in saved_paths:
            file_path = Path(saved_path)
            uploaded_image = UploadedImage(
                folder_id=brand_style_folder.id,
                folder_type="brand_style",
                filename=file_path.name,
                file_path=saved_path,
                file_size=file_path.stat().st_size if file_path.exists() else 0,
            )
            db.add(uploaded_image)

        db.commit()
        db.refresh(brand_style_folder)

        logger.info(f"Brand style images uploaded successfully for user {current_user.id}: {len(saved_paths)} images")

        return BrandStyleUploadResponse(
            message=f"Brand style images uploaded successfully ({len(saved_paths)} images)",
            count=len(saved_paths),
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading brand style images: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "UPLOAD_FAILED",
                    "message": "Failed to upload brand style images",
                }
            },
        )


@router.get("", response_model=BrandStyleListResponse)
async def get_brand_styles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrandStyleListResponse:
    """
    Get list of brand style images for the current user.

    Args:
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        BrandStyleListResponse with list of uploaded images

    Raises:
        HTTPException: 401 if not authenticated, 500 if server error
    """
    try:
        # Query brand style folder for user
        brand_style_folder = db.query(BrandStyleFolder).filter(BrandStyleFolder.user_id == current_user.id).first()

        if not brand_style_folder:
            return BrandStyleListResponse(images=[])

        # Query uploaded images for this folder
        uploaded_images = db.query(UploadedImage).filter(
            UploadedImage.folder_id == brand_style_folder.id,
            UploadedImage.folder_type == "brand_style"
        ).all()

        # Build response with image URLs
        image_responses = []
        for image in uploaded_images:
            # Get the actual filename from the file_path (this is what was actually saved)
            # The file_path might be relative or absolute, so extract just the filename
            actual_filename = Path(image.file_path).name
            
            # Generate URL: /api/assets/users/{user_id}/brand_styles/{filename}
            # Use the actual saved filename to ensure the URL matches the file on disk
            image_url = f"/api/assets/users/{current_user.id}/brand_styles/{actual_filename}"
            
            logger.debug(f"Brand style image URL: {image_url}, stored filename: {image.filename}, actual filename: {actual_filename}, file_path: {image.file_path}")
            
            image_responses.append(
                UploadedImageResponse(
                    id=image.id,
                    filename=actual_filename,  # Use actual filename that matches the saved file
                    url=image_url,
                    uploaded_at=image.uploaded_at,
                )
            )

        return BrandStyleListResponse(images=image_responses)

    except Exception as e:
        logger.error(f"Error getting brand style images: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "GET_FAILED",
                    "message": "Failed to retrieve brand style images",
                }
            },
        )


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_brand_styles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete all brand style images for the current user.

    Args:
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 401 if not authenticated, 500 if server error
    """
    try:
        # Query brand style folder for user
        brand_style_folder = db.query(BrandStyleFolder).filter(BrandStyleFolder.user_id == current_user.id).first()

        if not brand_style_folder:
            return {"message": "No brand style images found to delete"}

        # Delete all related uploaded images from database
        db.query(UploadedImage).filter(
            UploadedImage.folder_id == brand_style_folder.id,
            UploadedImage.folder_type == "brand_style"
        ).delete()

        # Delete folder from database
        db.delete(brand_style_folder)
        db.commit()

        # Delete physical folder from disk
        try:
            delete_user_folder(current_user.id, "brand_styles")
        except Exception as e:
            logger.warning(f"Error deleting brand style folder from disk: {e}")

        logger.info(f"Brand style images deleted successfully for user {current_user.id}")

        return {"message": "Brand style images deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting brand style images: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "DELETE_FAILED",
                    "message": "Failed to delete brand style images",
                }
            },
        )


@router.post("/extract", status_code=status.HTTP_200_OK, response_model=BrandStyleExtractResponse)
async def extract_brand_style_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrandStyleExtractResponse:
    """
    Extract brand style information from user's uploaded brand style images.
    
    Args:
        current_user: Current authenticated user (from dependency)
        db: Database session
        
    Returns:
        BrandStyleExtractResponse with extracted style JSON and status
        
    Raises:
        HTTPException: 404 if no brand style folder exists, 500 if extraction fails
    """
    try:
        # Load user's brand style folder
        brand_style_folder = db.query(BrandStyleFolder).filter(
            BrandStyleFolder.user_id == current_user.id
        ).first()
        
        if not brand_style_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NO_BRAND_STYLE_FOLDER",
                        "message": "No brand style images uploaded. Please upload brand style images first.",
                    }
                },
            )
        
        # Check if extraction is needed (caching logic)
        # Re-extract if: no JSON exists, status is failed, or folder was updated after extraction
        needs_extraction = (
            brand_style_folder.extracted_style_json is None
            or brand_style_folder.extraction_status == ExtractionStatus.FAILED
            or (
                brand_style_folder.extracted_at is not None
                and brand_style_folder.uploaded_at > brand_style_folder.extracted_at
            )
        )
        
        if not needs_extraction and brand_style_folder.extraction_status == ExtractionStatus.COMPLETED:
            logger.info(f"Using cached brand style JSON for user {current_user.id}")
            return BrandStyleExtractResponse(
                message="Brand style JSON retrieved from cache",
                extracted_style_json=brand_style_folder.extracted_style_json,
                extraction_status=brand_style_folder.extraction_status,
                extracted_at=brand_style_folder.extracted_at,
            )
        
        # Load brand style images
        uploaded_images = db.query(UploadedImage).filter(
            UploadedImage.folder_id == brand_style_folder.id,
            UploadedImage.folder_type == "brand_style"
        ).all()
        
        if not uploaded_images:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "NO_IMAGES",
                        "message": "No brand style images found in folder",
                    }
                },
            )
        
        # Get image file paths
        image_paths = [Path(img.file_path) for img in uploaded_images]
        
        # Update status to pending
        brand_style_folder.extraction_status = ExtractionStatus.PENDING
        db.commit()
        
        try:
            # Extract brand style using Vision LLM
            logger.info(f"Extracting brand style for user {current_user.id} from {len(image_paths)} images")
            brand_style_json = await extract_brand_style(image_paths)
            
            # Convert Pydantic model to dict for JSON storage
            style_dict = brand_style_json.model_dump()
            
            # Store extracted JSON in database
            brand_style_folder.extracted_style_json = style_dict
            brand_style_folder.extraction_status = ExtractionStatus.COMPLETED
            brand_style_folder.extracted_at = datetime.utcnow()
            db.commit()
            
            # Track Vision LLM cost
            cost = VISION_MODEL_COST_PER_IMAGE * len(image_paths)
            track_vision_llm_cost(
                db=db,
                user_id=current_user.id,
                cost=cost,
                operation_type="brand_style_extraction",
                image_count=len(image_paths)
            )
            
            logger.info(f"Brand style extraction completed for user {current_user.id} (cost: ${cost:.4f})")
            
            return BrandStyleExtractResponse(
                message=f"Brand style extracted successfully from {len(image_paths)} images",
                extracted_style_json=style_dict,
                extraction_status=brand_style_folder.extraction_status,
                extracted_at=brand_style_folder.extracted_at,
            )
            
        except Exception as e:
            logger.error(f"Error extracting brand style: {e}", exc_info=True)
            
            # Update status to failed
            brand_style_folder.extraction_status = ExtractionStatus.FAILED
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "EXTRACTION_FAILED",
                        "message": f"Failed to extract brand style: {str(e)}",
                    }
                },
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in brand style extraction: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "EXTRACTION_ERROR",
                    "message": "An unexpected error occurred during brand style extraction",
                }
            },
        )

