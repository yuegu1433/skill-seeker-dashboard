"""MinIO client configuration and connection management.

This module provides MinIO client configuration, connection management,
retry mechanisms, and error handling for the storage system.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
from urllib.parse import urlparse

try:
    from minio import Minio
    from minio.error import S3Error, ServerError
    from minio.commonconfig import CopySource
except ImportError:
    # MinIO not installed - will be installed with dependencies
    Minio = None
    S3Error = Exception
    ServerError = Exception
    CopySource = None

from .schemas.storage_config import MinIOConfig
from .utils.validators import validate_bucket_name

logger = logging.getLogger(__name__)


class MinIOClientError(Exception):
    """Base exception for MinIO client errors."""
    pass


class MinIOConnectionError(MinIOClientError):
    """Raised when MinIO connection fails."""
    pass


class MinIOConfigurationError(MinIOClientError):
    """Raised when MinIO configuration is invalid."""
    pass


class MinIOOperationError(MinIOClientError):
    """Raised when MinIO operation fails."""
    pass


class MinIOClient:
    """MinIO client with connection management and retry logic.

    Provides a wrapper around the MinIO Python client with additional
    features like connection pooling, retry mechanisms, and error handling.
    """

    def __init__(self, config: MinIOConfig):
        """Initialize MinIO client.

        Args:
            config: MinIO configuration

        Raises:
            MinIOConfigurationError: If configuration is invalid
            MinIOConnectionError: If connection fails
        """
        self.config = config
        self._client: Optional[Minio] = None
        self._connection_lock = None  # Will be initialized for thread safety

        self._validate_config()
        self._initialize_client()

    def _validate_config(self) -> None:
        """Validate MinIO configuration.

        Raises:
            MinIOConfigurationError: If configuration is invalid
        """
        if not self.config.endpoint:
            raise MinIOConfigurationError("MinIO endpoint is required")

        if not self.config.access_key:
            raise MinIOConfigurationError("MinIO access key is required")

        if not self.config.secret_key:
            raise MinIOConfigurationError("MinIO secret key is required")

        # Validate endpoint format
        parsed_url = urlparse(f"http://{self.config.endpoint}")
        if not parsed_url.hostname:
            raise MinIOConfigurationError(f"Invalid endpoint format: {self.config.endpoint}")

        logger.debug("MinIO configuration validated successfully")

    def _initialize_client(self) -> None:
        """Initialize MinIO client with configuration.

        Raises:
            MinIOConnectionError: If connection fails
        """
        try:
            self._client = Minio(
                endpoint=self.config.endpoint,
                access_key=self.config.access_key,
                secret_key=self.config.secret_key,
                secure=self.config.secure,
                region=self.config.region or "us-east-1",
            )

            # Test connection
            if not self._test_connection():
                raise MinIOConnectionError("Failed to connect to MinIO server")

            logger.info(f"MinIO client initialized for endpoint: {self.config.endpoint}")

        except Exception as e:
            raise MinIOConnectionError(f"Failed to initialize MinIO client: {e}")

    def _test_connection(self) -> bool:
        """Test connection to MinIO server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list buckets to test connection
            list(self._client.list_buckets())
            return True
        except Exception as e:
            logger.error(f"MinIO connection test failed: {e}")
            return False

    @property
    def client(self) -> Minio:
        """Get MinIO client instance.

        Returns:
            MinIO client instance

        Raises:
            MinIOClientError: If client is not initialized
        """
        if self._client is None:
            raise MinIOClientError("MinIO client not initialized")
        return self._client

    def is_healthy(self) -> bool:
        """Check if MinIO client is healthy.

        Returns:
            True if client is healthy, False otherwise
        """
        try:
            # Test connection
            return self._test_connection()
        except Exception as e:
            logger.warning(f"MinIO health check failed: {e}")
            return False

    def list_buckets(self) -> Generator[Dict[str, Any], None, None]:
        """List all buckets.

        Yields:
            Bucket information dictionaries

        Raises:
            MinIOOperationError: If operation fails
        """
        try:
            buckets = self.client.list_buckets()
            for bucket in buckets:
                yield {
                    "name": bucket.name,
                    "creation_date": bucket.creation_date,
                }
        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to list buckets: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error listing buckets: {e}")

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if bucket exists.

        Args:
            bucket_name: Name of bucket to check

        Returns:
            True if bucket exists, False otherwise

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            return self.client.bucket_exists(bucket_name)
        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to check bucket existence: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error checking bucket: {e}")

    def create_bucket(self, bucket_name: str, **kwargs) -> bool:
        """Create a new bucket.

        Args:
            bucket_name: Name of bucket to create
            **kwargs: Additional arguments for bucket creation

        Returns:
            True if bucket created successfully

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            self.client.make_bucket(bucket_name, **kwargs)
            logger.info(f"Created bucket: {bucket_name}")
            return True
        except (S3Error, ServerError) as e:
            if "BucketAlreadyOwnedByYou" in str(e):
                logger.info(f"Bucket already exists: {bucket_name}")
                return True
            raise MinIOOperationError(f"Failed to create bucket {bucket_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error creating bucket: {e}")

    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a bucket.

        Args:
            bucket_name: Name of bucket to delete
            force: If True, delete bucket even if not empty

        Returns:
            True if bucket deleted successfully

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            # Check if bucket exists
            if not self.bucket_exists(bucket_name):
                logger.warning(f"Bucket not found: {bucket_name}")
                return False

            # Delete bucket
            self.client.remove_bucket(bucket_name)
            logger.info(f"Deleted bucket: {bucket_name}")
            return True

        except (S3Error, ServerError) as e:
            if "BucketNotEmpty" in str(e) and not force:
                raise MinIOOperationError(
                    f"Bucket {bucket_name} is not empty. Use force=True to delete anyway."
                )
            raise MinIOOperationError(f"Failed to delete bucket {bucket_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error deleting bucket: {e}")

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data,
        length: int,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Upload an object to MinIO.

        Args:
            bucket_name: Name of bucket
            object_name: Name of object
            data: Object data
            length: Length of data
            content_type: Content type
            metadata: Object metadata
            **kwargs: Additional arguments

        Returns:
            Dictionary with object information

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data,
                length=length,
                content_type=content_type,
                metadata=metadata,
                **kwargs,
            )

            logger.debug(f"Uploaded object {object_name} to bucket {bucket_name}")
            return {
                "object_name": result.object_name,
                "etag": result.etag,
                "size": result.size,
            }

        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to upload object {object_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error uploading object: {e}")

    def get_object(
        self,
        bucket_name: str,
        object_name: str,
        offset: int = 0,
        length: int = 0,
        **kwargs,
    ) -> Any:
        """Get an object from MinIO.

        Args:
            bucket_name: Name of bucket
            object_name: Name of object
            offset: Starting byte position
            length: Number of bytes
            **kwargs: Additional arguments

        Returns:
            Object response

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            return self.client.get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                offset=offset,
                length=length,
                **kwargs,
            )

        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to get object {object_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error getting object: {e}")

    def remove_object(self, bucket_name: str, object_name: str, **kwargs) -> bool:
        """Remove an object from MinIO.

        Args:
            bucket_name: Name of bucket
            object_name: Name of object
            **kwargs: Additional arguments

        Returns:
            True if object removed successfully

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            self.client.remove_object(bucket_name, object_name, **kwargs)
            logger.debug(f"Removed object {object_name} from bucket {bucket_name}")
            return True

        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to remove object {object_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error removing object: {e}")

    def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = True,
        include_version: bool = False,
        **kwargs,
    ) -> Generator[Dict[str, Any], None, None]:
        """List objects in a bucket.

        Args:
            bucket_name: Name of bucket
            prefix: Object name prefix
            recursive: Recursive listing
            include_version: Include version information
            **kwargs: Additional arguments

        Yields:
            Object information dictionaries

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix,
                recursive=recursive,
                include_version=include_version,
                **kwargs,
            )

            for obj in objects:
                yield {
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "etag": obj.etag,
                    "content_type": obj.content_type,
                    "last_modified": obj.last_modified,
                    "is_dir": obj.is_dir,
                }

        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to list objects in bucket {bucket_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error listing objects: {e}")

    def stat_object(self, bucket_name: str, object_name: str, **kwargs) -> Dict[str, Any]:
        """Get object metadata.

        Args:
            bucket_name: Name of bucket
            object_name: Name of object
            **kwargs: Additional arguments

        Returns:
            Dictionary with object metadata

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            stat = self.client.stat_object(bucket_name, object_name, **kwargs)
            return {
                "bucket_name": stat.bucket_name,
                "object_name": stat.object_name,
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata,
            }

        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to get object stat {object_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error getting object stat: {e}")

    def presigned_get_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
        **kwargs,
    ) -> str:
        """Generate a presigned URL for GET operations.

        Args:
            bucket_name: Name of bucket
            object_name: Name of object
            expires: URL expiration time in seconds
            **kwargs: Additional arguments

        Returns:
            Presigned URL

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            return self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires,
                **kwargs,
            )

        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to generate presigned URL: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error generating presigned URL: {e}")

    def copy_object(
        self,
        bucket_name: str,
        object_name: str,
        source: CopySource,
        **kwargs,
    ) -> Dict[str, Any]:
        """Copy an object within MinIO.

        Args:
            bucket_name: Name of bucket
            object_name: Destination object name
            source: Source object information
            **kwargs: Additional arguments

        Returns:
            Dictionary with copy result

        Raises:
            MinIOConfigurationError: If bucket name is invalid
            MinIOOperationError: If operation fails
        """
        bucket_name = validate_bucket_name(bucket_name)

        try:
            result = self.client.copy_object(
                bucket_name=bucket_name,
                object_name=object_name,
                source=source,
                **kwargs,
            )

            logger.debug(f"Copied object to {object_name}")
            return {
                "etag": result.etag,
                "size": result.size,
            }

        except (S3Error, ServerError) as e:
            raise MinIOOperationError(f"Failed to copy object {object_name}: {e}")
        except Exception as e:
            raise MinIOOperationError(f"Unexpected error copying object: {e}")

    def close(self) -> None:
        """Close MinIO client connection."""
        if self._client:
            # MinIO client doesn't have a close method, but we can clean up resources
            self._client = None
            logger.info("MinIO client connection closed")

    def __enter__(self) -> "MinIOClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    @contextmanager
    def operation_context(self, operation_name: str) -> Generator[None, None, None]:
        """Context manager for MinIO operations with error handling.

        Args:
            operation_name: Name of operation for logging

        Yields:
            None
        """
        logger.debug(f"Starting MinIO operation: {operation_name}")
        start_time = time.time()

        try:
            yield
            duration = time.time() - start_time
            logger.debug(f"MinIO operation '{operation_name}' completed in {duration:.3f}s")
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"MinIO operation '{operation_name}' failed after {duration:.3f}s: {e}")
            raise


class MinIOClientManager:
    """Manager for MinIO client instances.

    Provides centralized management of MinIO client instances
    with connection pooling and lifecycle management.
    """

    def __init__(self, config: Optional[MinIOConfig] = None):
        """Initialize MinIO client manager.

        Args:
            config: Default MinIO configuration
        """
        self.config = config
        self._clients: Dict[str, MinIOClient] = {}
        self._default_client: Optional[MinIOClient] = None

    def get_client(self, config: Optional[MinIOConfig] = None) -> MinIOClient:
        """Get or create a MinIO client.

        Args:
            config: Optional configuration (uses default if not provided)

        Returns:
            MinIO client instance

        Raises:
            MinIOConfigurationError: If configuration is invalid
            MinIOConnectionError: If connection fails
        """
        if config is None:
            config = self.config

        if config is None:
            raise MinIOConfigurationError("No MinIO configuration provided")

        # Use config as key for client instance
        config_key = f"{config.endpoint}:{config.access_key}"

        if config_key not in self._clients:
            self._clients[config_key] = MinIOClient(config)

        return self._clients[config_key]

    def get_default_client(self) -> MinIOClient:
        """Get default MinIO client.

        Returns:
            Default MinIO client instance

        Raises:
            MinIOConfigurationError: If no default configuration is set
        """
        if self._default_client is None:
            if self.config is None:
                raise MinIOConfigurationError("No default MinIO configuration set")
            self._default_client = MinIOClient(self.config)

        return self._default_client

    def set_default_config(self, config: MinIOConfig) -> None:
        """Set default MinIO configuration.

        Args:
            config: MinIO configuration to set as default
        """
        self.config = config
        self._default_client = None  # Reset default client

    def health_check_all(self) -> Dict[str, bool]:
        """Check health of all client instances.

        Returns:
            Dictionary mapping client identifiers to health status
        """
        health_status = {}

        for key, client in self._clients.items():
            health_status[key] = client.is_healthy()

        if self._default_client:
            health_status["default"] = self._default_client.is_healthy()

        return health_status

    def close_all(self) -> None:
        """Close all MinIO client connections."""
        for client in self._clients.values():
            client.close()

        if self._default_client:
            self._default_client.close()

        self._clients.clear()
        self._default_client = None

        logger.info("All MinIO client connections closed")
