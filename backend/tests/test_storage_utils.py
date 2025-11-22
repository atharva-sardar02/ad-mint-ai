"""
Unit tests for storage utilities.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi import UploadFile

from app.utils.storage import (
    ensure_user_directory,
    validate_image_file,
    validate_folder_size,
    validate_image_count,
    save_uploaded_images,
    delete_user_folder,
    get_user_folder_path,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_FOLDER_SIZE_BYTES,
    MAX_IMAGES_PER_FOLDER,
)


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing."""
    def _create_mock(filename: str, content_type: str, content: bytes):
        file = Mock(spec=UploadFile)
        file.filename = filename
        file.content_type = content_type
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        return file
    return _create_mock


def test_validate_image_file_valid():
    """Test validate_image_file with valid image files."""
    file1 = Mock(spec=UploadFile)
    file1.content_type = "image/jpeg"
    file1.filename = "test.jpg"
    
    file2 = Mock(spec=UploadFile)
    file2.content_type = "image/png"
    file2.filename = "test.png"
    
    file3 = Mock(spec=UploadFile)
    file3.content_type = "image/webp"
    file3.filename = "test.webp"
    
    assert validate_image_file(file1) is True
    assert validate_image_file(file2) is True
    assert validate_image_file(file3) is True


def test_validate_image_file_invalid():
    """Test validate_image_file with invalid image files."""
    file1 = Mock(spec=UploadFile)
    file1.content_type = "text/plain"
    file1.filename = "test.txt"
    
    file2 = Mock(spec=UploadFile)
    file2.content_type = "image/jpeg"
    file2.filename = "test.pdf"
    
    assert validate_image_file(file1) is False
    assert validate_image_file(file2) is False


def test_validate_image_count_valid():
    """Test validate_image_count with valid counts."""
    files = [Mock(spec=UploadFile) for _ in range(10)]
    assert validate_image_count(files, max_count=50) is True
    assert validate_image_count(files, max_count=10) is True


def test_validate_image_count_invalid():
    """Test validate_image_count with invalid counts."""
    files = [Mock(spec=UploadFile) for _ in range(60)]
    assert validate_image_count(files, max_count=50) is False


@pytest.mark.asyncio
async def test_validate_folder_size_valid(mock_upload_file):
    """Test validate_folder_size with valid folder sizes."""
    files = [
        mock_upload_file("test1.jpg", "image/jpeg", b"x" * (10 * 1024 * 1024)),  # 10MB
        mock_upload_file("test2.jpg", "image/jpeg", b"x" * (20 * 1024 * 1024)),  # 20MB
    ]
    result = await validate_folder_size(files, max_size_mb=100)
    assert result is True


@pytest.mark.asyncio
async def test_validate_folder_size_invalid(mock_upload_file):
    """Test validate_folder_size with invalid folder sizes."""
    files = [
        mock_upload_file("test1.jpg", "image/jpeg", b"x" * (60 * 1024 * 1024)),  # 60MB
        mock_upload_file("test2.jpg", "image/jpeg", b"x" * (50 * 1024 * 1024)),  # 50MB (total 110MB > 100MB)
    ]
    result = await validate_folder_size(files, max_size_mb=100)
    assert result is False


def test_ensure_user_directory(tmp_path):
    """Test ensure_user_directory creates directories correctly."""
    with patch("app.utils.storage.STORAGE_BASE_DIR", tmp_path):
        user_id = "test-user-123"
        folder_type = "brand_styles"
        
        user_dir = ensure_user_directory(user_id, folder_type)
        
        assert user_dir.exists()
        assert user_dir.is_dir()
        assert user_dir.name == folder_type
        assert user_dir.parent.name == user_id


def test_get_user_folder_path():
    """Test get_user_folder_path returns correct path."""
    user_id = "test-user-123"
    folder_type = "brand_styles"
    
    folder_path = get_user_folder_path(user_id, folder_type)
    
    assert str(folder_path).endswith(f"users/{user_id}/{folder_type}")


@pytest.mark.asyncio
async def test_save_uploaded_images(tmp_path, mock_upload_file):
    """Test save_uploaded_images saves files correctly."""
    with patch("app.utils.storage.STORAGE_BASE_DIR", tmp_path):
        user_id = "test-user-123"
        folder_type = "brand_styles"
        
        files = [
            mock_upload_file("test1.jpg", "image/jpeg", b"fake image content 1"),
            mock_upload_file("test2.png", "image/png", b"fake image content 2"),
        ]
        
        saved_paths = await save_uploaded_images(user_id, files, folder_type)
        
        assert len(saved_paths) == 2
        for saved_path in saved_paths:
            assert Path(saved_path).exists()
            assert saved_path.startswith("backend/assets/users")


def test_delete_user_folder(tmp_path):
    """Test delete_user_folder deletes directories correctly."""
    with patch("app.utils.storage.STORAGE_BASE_DIR", tmp_path):
        user_id = "test-user-123"
        folder_type = "brand_styles"
        
        # Create directory first
        user_dir = ensure_user_directory(user_id, folder_type)
        test_file = user_dir / "test.jpg"
        test_file.write_bytes(b"test content")
        
        assert user_dir.exists()
        
        # Delete directory
        delete_user_folder(user_id, folder_type)
        
        assert not user_dir.exists()

