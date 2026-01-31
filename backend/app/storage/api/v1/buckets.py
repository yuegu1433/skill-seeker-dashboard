"""Buckets API endpoints.

This module provides REST API endpoints for bucket management operations
including creation, deletion, listing, and configuration.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.client import MinIOClient, MinIOClientError
from backend.app.database.session import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/buckets", tags=["buckets"])


@router.get(
    "/list",
    summary="List all buckets",
    description="List all storage buckets in the system",
)
async def list_buckets(
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """List all storage buckets.

    Args:
        minio_client: MinIO client dependency

    Returns:
        List of buckets with information

    Raises:
        HTTPException: If listing fails
    """
    try:
        buckets = []
        for bucket_info in minio_client.list_buckets():
            buckets.append(
                {
                    "name": bucket_info["name"],
                    "creation_date": bucket_info["creation_date"].isoformat()
                    if bucket_info["creation_date"]
                    else None,
                }
            )

        logger.info(f"Buckets listed: count={len(buckets)}")

        return {
            "success": True,
            "buckets": buckets,
            "message": "Buckets retrieved successfully",
        }

    except MinIOClientError as e:
        logger.error(f"List buckets failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"List buckets failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/create",
    summary="Create a bucket",
    description="Create a new storage bucket",
)
async def create_bucket(
    bucket_name: str = Query(..., description="Bucket name"),
    region: Optional[str] = Query(None, description="Bucket region"),
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """Create a new storage bucket.

    Args:
        bucket_name: Name of the bucket to create
        region: Optional region for the bucket
        minio_client: MinIO client dependency

    Returns:
        Creation result

    Raises:
        HTTPException: If creation fails or bucket already exists
    """
    try:
        # Create bucket
        result = minio_client.create_bucket(bucket_name, region=region)

        if not result:
            raise HTTPException(status_code=400, detail="Failed to create bucket")

        logger.info(f"Bucket created: name={bucket_name}, region={region}")

        return {
            "success": True,
            "bucket_name": bucket_name,
            "region": region,
            "message": "Bucket created successfully",
        }

    except HTTPException:
        raise
    except MinIOClientError as e:
        logger.error(f"Create bucket failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Create bucket failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/delete",
    summary="Delete a bucket",
    description="Delete a storage bucket",
)
async def delete_bucket(
    bucket_name: str = Query(..., description="Bucket name"),
    force: bool = Query(False, description="Force deletion even if bucket is not empty"),
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """Delete a storage bucket.

    Args:
        bucket_name: Name of the bucket to delete
        force: Force deletion even if bucket is not empty
        minio_client: MinIO client dependency

    Returns:
        Deletion result

    Raises:
        HTTPException: If bucket not found or deletion fails
    """
    try:
        # Delete bucket
        result = minio_client.delete_bucket(bucket_name, force=force)

        if not result:
            raise HTTPException(status_code=404, detail="Bucket not found")

        logger.info(f"Bucket deleted: name={bucket_name}, force={force}")

        return {
            "success": True,
            "bucket_name": bucket_name,
            "force": force,
            "message": "Bucket deleted successfully",
        }

    except HTTPException:
        raise
    except MinIOClientError as e:
        logger.error(f"Delete bucket failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Delete bucket failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/exists",
    summary="Check if bucket exists",
    description="Check if a storage bucket exists",
)
async def check_bucket_exists(
    bucket_name: str = Query(..., description="Bucket name"),
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """Check if a storage bucket exists.

    Args:
        bucket_name: Name of the bucket to check
        minio_client: MinIO client dependency

    Returns:
        Bucket existence status

    Raises:
        HTTPException: If check fails
    """
    try:
        # Check bucket existence
        exists = minio_client.bucket_exists(bucket_name)

        logger.info(f"Bucket exists check: name={bucket_name}, exists={exists}")

        return {
            "success": True,
            "bucket_name": bucket_name,
            "exists": exists,
            "message": "Bucket check completed",
        }

    except MinIOClientError as e:
        logger.error(f"Check bucket exists failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Check bucket exists failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{bucket_name}/objects",
    summary="List objects in bucket",
    description="List all objects in a storage bucket",
)
async def list_bucket_objects(
    bucket_name: str = ...,
    prefix: Optional[str] = Query(None, description="Object name prefix"),
    recursive: bool = Query(True, description="Recursive listing"),
    include_version: bool = Query(False, description="Include version information"),
    max_keys: int = Query(1000, ge=1, le=10000, description="Maximum number of keys to return"),
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """List all objects in a storage bucket.

    Args:
        bucket_name: Bucket name
        prefix: Optional object name prefix
        recursive: Recursive listing
        include_version: Include version information
        max_keys: Maximum number of keys to return
        minio_client: MinIO client dependency

    Returns:
        List of objects in the bucket

    Raises:
        HTTPException: If listing fails
    """
    try:
        objects = []
        count = 0

        for obj_info in minio_client.list_objects(
            bucket_name=bucket_name,
            prefix=prefix or "",
            recursive=recursive,
            include_version=include_version,
        ):
            if count >= max_keys:
                break

            objects.append(
                {
                    "object_name": obj_info["object_name"],
                    "size": obj_info["size"],
                    "etag": obj_info["etag"],
                    "content_type": obj_info["content_type"],
                    "last_modified": obj_info["last_modified"].isoformat()
                    if obj_info["last_modified"]
                    else None,
                    "is_dir": obj_info["is_dir"],
                }
            )
            count += 1

        logger.info(
            f"Bucket objects listed: bucket={bucket_name}, count={count}, "
            f"prefix={prefix}, recursive={recursive}"
        )

        return {
            "success": True,
            "bucket_name": bucket_name,
            "objects": objects,
            "total_returned": count,
            "message": "Objects retrieved successfully",
        }

    except MinIOClientError as e:
        logger.error(f"List bucket objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"List bucket objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{bucket_name}/objects/count",
    summary="Count objects in bucket",
    description="Count all objects in a storage bucket",
)
async def count_bucket_objects(
    bucket_name: str = ...,
    prefix: Optional[str] = Query(None, description="Object name prefix"),
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """Count all objects in a storage bucket.

    Args:
        bucket_name: Bucket name
        prefix: Optional object name prefix
        minio_client: MinIO client dependency

    Returns:
        Object count and total size

    Raises:
        HTTPException: If counting fails
    """
    try:
        count = 0
        total_size = 0

        for obj_info in minio_client.list_objects(
            bucket_name=bucket_name,
            prefix=prefix or "",
            recursive=True,
        ):
            count += 1
            total_size += obj_info["size"]

        logger.info(
            f"Bucket objects counted: bucket={bucket_name}, count={count}, "
            f"size={total_size}, prefix={prefix}"
        )

        return {
            "success": True,
            "bucket_name": bucket_name,
            "object_count": count,
            "total_size": total_size,
            "total_size_human": format_bytes(total_size),
            "prefix": prefix,
            "message": "Objects counted successfully",
        }

    except MinIOClientError as e:
        logger.error(f"Count bucket objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Count bucket objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{bucket_name}/objects/delete",
    summary="Delete objects from bucket",
    description="Delete multiple objects from a bucket",
)
async def delete_bucket_objects(
    bucket_name: str = ...,
    object_names: List[str] = Query(..., description="List of object names to delete"),
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """Delete multiple objects from a bucket.

    Args:
        bucket_name: Bucket name
        object_names: List of object names to delete
        minio_client: MinIO client dependency

    Returns:
        Deletion results

    Raises:
        HTTPException: If deletion fails
    """
    try:
        deleted_count = 0
        failed_count = 0

        for object_name in object_names:
            try:
                minio_client.remove_object(bucket_name, object_name)
                deleted_count += 1
            except Exception:
                failed_count += 1

        logger.info(
            f"Bucket objects deleted: bucket={bucket_name}, "
            f"deleted={deleted_count}, failed={failed_count}"
        )

        return {
            "success": True,
            "bucket_name": bucket_name,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "total_requested": len(object_names),
            "message": "Objects deletion completed",
        }

    except Exception as e:
        logger.error(f"Delete bucket objects failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Check MinIO health",
    description="Check the health status of the MinIO storage",
)
async def check_minio_health(
    minio_client: MinIOClient = Depends(get_minio_client),
):
    """Check the health status of the MinIO storage.

    Args:
        minio_client: MinIO client dependency

    Returns:
        Health status information

    Raises:
        HTTPException: If health check fails
    """
    try:
        # Check MinIO health
        is_healthy = minio_client.is_healthy()

        # Get bucket count
        bucket_count = 0
        if is_healthy:
            buckets = list(minio_client.list_buckets())
            bucket_count = len(buckets)

        status = "healthy" if is_healthy else "unhealthy"

        logger.info(f"MinIO health check: status={status}, buckets={bucket_count}")

        return {
            "success": True,
            "status": status,
            "is_healthy": is_healthy,
            "bucket_count": bucket_count,
            "message": f"MinIO is {status}",
        }

    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to format bytes
def format_bytes(size: int) -> str:
    """Format bytes to human-readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


# Dependency to get MinIO client
def get_minio_client() -> MinIOClient:
    """Get MinIO client instance.

    Returns:
        MinIOClient instance
    """
    # In a real application, this would be injected via FastAPI's dependency system
    # For now, we'll return a placeholder
    # This should be replaced with actual dependency injection
    from backend.app.storage.client import MinIOClient
    from backend.app.storage.schemas.storage_config import MinIOConfig

    # This is a placeholder - in production, use proper DI
    raise NotImplementedError(
        "MinIO client dependency not configured. "
        "Configure FastAPI dependency injection for MinIOClient."
    )
