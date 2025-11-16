"""
S3 storage service for video and thumbnail files.
"""
import logging
from pathlib import Path
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Storage:
    """S3 storage service for uploading and downloading video files."""
    
    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        self.bucket_name = settings.AWS_S3_VIDEO_BUCKET
        self.region = settings.AWS_REGION or "us-east-1"
        
        # Initialize S3 client
        config = Config(
            region_name=self.region,
            retries={
                'max_attempts': 3,
                'mode': 'standard'
            }
        )
        
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            # Use access keys
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=config
            )
        else:
            # Use IAM role (for EC2 instance)
            self.s3_client = boto3.client('s3', config=config)
        
        logger.info(f"S3 storage initialized for bucket: {self.bucket_name} (region: {self.region})")
    
    def upload_file(self, local_path: str, s3_key: str, content_type: Optional[str] = None) -> str:
        """
        Upload a file to S3.
        
        Args:
            local_path: Local file path to upload
            s3_key: S3 object key (path in bucket)
            content_type: Optional content type (e.g., 'video/mp4', 'image/jpeg')
        
        Returns:
            str: S3 object URL
        
        Raises:
            RuntimeError: If upload fails
        """
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                raise RuntimeError(f"Local file not found: {local_path}")
            
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            logger.info(f"Uploading {local_path} to s3://{self.bucket_name}/{s3_key}")
            self.s3_client.upload_file(
                str(local_file),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate S3 URL
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"File uploaded successfully: {s3_url}")
            return s3_url
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 upload failed ({error_code}): {e}")
            raise RuntimeError(f"S3 upload failed: {error_code}")
        except BotoCoreError as e:
            logger.error(f"S3 client error during upload: {e}")
            raise RuntimeError(f"S3 upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}", exc_info=True)
            raise RuntimeError(f"S3 upload failed: {str(e)}")
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for downloading a file from S3.
        
        Args:
            s3_key: S3 object key (path in bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            str: Presigned URL
        
        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            logger.debug(f"Generated presigned URL for {s3_key} (expires in {expiration}s)")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise RuntimeError(f"Failed to generate presigned URL: {str(e)}")
    
    def delete_file(self, s3_key: str) -> None:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key (path in bucket)
        
        Raises:
            RuntimeError: If deletion fails
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted file from S3: {s3_key}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code != 'NoSuchKey':
                logger.error(f"S3 delete failed ({error_code}): {e}")
                raise RuntimeError(f"S3 delete failed: {error_code}")
            else:
                logger.warning(f"File not found in S3 (already deleted?): {s3_key}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 delete: {e}", exc_info=True)
            raise RuntimeError(f"S3 delete failed: {str(e)}")
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key (path in bucket)
        
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404' or error_code == 'NoSuchKey':
                return False
            logger.error(f"Error checking file existence: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test S3 connection by attempting to list bucket contents.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.debug("S3 connection test successful")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 connection test failed ({error_code}): {e}")
            return False
        except Exception as e:
            logger.error(f"S3 connection test error: {e}")
            return False


# Global S3 storage instance (initialized on first use)
_s3_storage: Optional[S3Storage] = None


def get_s3_storage() -> S3Storage:
    """Get or create S3 storage instance."""
    global _s3_storage
    if _s3_storage is None:
        _s3_storage = S3Storage()
    return _s3_storage

