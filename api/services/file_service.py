"""MinIO file storage service."""

import logging
from typing import Optional
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class FileService:
    """Service for managing files in MinIO object storage."""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False
    ):
        """
        Initialize MinIO client.
        
        Args:
            endpoint: MinIO server endpoint
            access_key: Access key
            secret_key: Secret key
            bucket_name: Default bucket name
            secure: Use HTTPS if True
        """
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self._ensure_bucket_exists()
        logger.info(f"File service initialized with bucket: {bucket_name}")
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_file(
        self,
        file_path: str,
        object_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to MinIO.
        
        Args:
            file_path: Path to local file
            object_name: Object name in bucket
            content_type: MIME type
            
        Returns:
            Object URL
        """
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            logger.info(f"Uploaded file: {object_name}")
            return f"{self.endpoint}/{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str):
        """
        Download file from MinIO.
        
        Args:
            object_name: Object name in bucket
            file_path: Path to save file locally
        """
        try:
            self.client.fget_object(
                self.bucket_name,
                object_name,
                file_path
            )
            logger.info(f"Downloaded file: {object_name}")
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Generate presigned URL for file access.
        
        Args:
            object_name: Object name in bucket
            expires: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def delete_file(self, object_name: str):
        """Delete file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def list_files(self, prefix: Optional[str] = None) -> list:
        """List files in bucket."""
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise
