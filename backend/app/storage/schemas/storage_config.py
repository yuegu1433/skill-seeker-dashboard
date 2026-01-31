"""Storage configuration schemas for MinIO storage system.

This module contains Pydantic models for validating storage configuration
settings in the MinIO storage system.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class MinIOConfig(BaseModel):
    """Configuration for MinIO client connection."""

    endpoint: str = Field(..., description="MinIO服务器地址")
    access_key: str = Field(..., description="访问密钥")
    secret_key: str = Field(..., description="秘密密钥")
    secure: bool = Field(default=False, description="是否使用HTTPS")
    region: Optional[str] = Field(None, description="区域")
    timeout: int = Field(default=30000, ge=1000, description="超时时间(毫秒)")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="重试次数")
    chunk_size: int = Field(default=10485760, ge=1024, description="分块大小(字节)")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class CacheConfig(BaseModel):
    """Configuration for caching system."""

    enabled: bool = Field(default=True, description="是否启用缓存")
    ttl: int = Field(default=3600, ge=60, description="缓存过期时间(秒)")
    max_size: int = Field(default=1000000, ge=1000, description="最大缓存条目数")
    compression_enabled: bool = Field(default=True, description="是否启用压缩")
    cleanup_interval: int = Field(default=1800, ge=300, description="清理间隔(秒)")
    hit_rate_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="命中率阈值")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BackupConfig(BaseModel):
    """Configuration for backup system."""

    enabled: bool = Field(default=True, description="是否启用备份")
    schedule: str = Field(default="daily", description="备份调度(cron表达式或预设)")
    retention_days: int = Field(default=30, ge=1, description="保留天数")
    compression_enabled: bool = Field(default=True, description="是否启用压缩")
    encryption_enabled: bool = Field(default=True, description="是否启用加密")
    verification_enabled: bool = Field(default=True, description="是否启用验证")
    backup_bucket: str = Field(default="skillseekers-archives", description="备份桶名")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class VersionConfig(BaseModel):
    """Configuration for version control system."""

    enabled: bool = Field(default=True, description="是否启用版本控制")
    max_versions: int = Field(default=10, ge=1, le=100, description="最大版本数")
    auto_cleanup: bool = Field(default=True, description="是否自动清理")
    cleanup_threshold_days: int = Field(default=90, ge=1, description="清理阈值(天)")
    compression_enabled: bool = Field(default=True, description="是否启用压缩")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class SecurityConfig(BaseModel):
    """Configuration for security settings."""

    encryption_enabled: bool = Field(default=True, description="是否启用加密")
    default_visibility: str = Field(default="private", description="默认可见性")
    allowed_content_types: list = Field(
        default_factory=lambda: [
            "text/plain",
            "text/markdown",
            "text/html",
            "application/json",
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/zip",
        ],
        description="允许的MIME类型",
    )
    max_file_size: int = Field(default=104857600, ge=1024, description="最大文件大小(字节)")
    checksum_validation: bool = Field(default=True, description="是否验证校验和")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class MonitoringConfig(BaseModel):
    """Configuration for monitoring and alerting."""

    enabled: bool = Field(default=True, description="是否启用监控")
    metrics_collection_interval: int = Field(default=60, ge=10, description="指标收集间隔(秒)")
    storage_threshold_warning: float = Field(default=0.8, ge=0.0, le=1.0, description="存储警告阈值")
    storage_threshold_critical: float = Field(default=0.9, ge=0.0, le=1.0, description="存储严重阈值")
    error_rate_threshold: float = Field(default=0.05, ge=0.0, le=1.0, description="错误率阈值")
    alert_webhook_url: Optional[str] = Field(None, description="告警Webhook URL")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class StorageConfig(BaseModel):
    """Complete storage system configuration."""

    minio: MinIOConfig = Field(..., description="MinIO配置")
    cache: CacheConfig = Field(default_factory=CacheConfig, description="缓存配置")
    backup: BackupConfig = Field(default_factory=BackupConfig, description="备份配置")
    version: VersionConfig = Field(default_factory=VersionConfig, description="版本控制配置")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="安全配置")
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig, description="监控配置")

    # System settings
    default_bucket: str = Field(default="skillseekers-skills", description="默认存储桶")
    temp_bucket: str = Field(default="skillseekers-temp", description="临时存储桶")
    archive_bucket: str = Field(default="skillseekers-archives", description="归档存储桶")

    # Performance settings
    max_concurrent_uploads: int = Field(default=10, ge=1, le=100, description="最大并发上传数")
    max_concurrent_downloads: int = Field(default=20, ge=1, le=200, description="最大并发下载数")
    chunk_upload_threshold: int = Field(default=10485760, ge=1024, description="分块上传阈值(字节)")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# Configuration templates
class ConfigTemplate(BaseModel):
    """Template for creating configurations."""

    name: str = Field(..., description="配置模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    config: StorageConfig = Field(..., description="配置内容")
    is_default: bool = Field(default=False, description="是否为默认模板")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configurations."""

    config: StorageConfig = Field(..., description="新配置")
    description: Optional[str] = Field(None, description="配置描述")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ConfigResponse(BaseModel):
    """Response model for configuration operations."""

    success: bool = Field(..., description="操作是否成功")
    config: Optional[StorageConfig] = Field(None, description="配置内容")
    message: Optional[str] = Field(None, description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# Bucket configuration schemas
class BucketConfig(BaseModel):
    """Configuration for storage buckets."""

    name: str = Field(..., description="桶名")
    bucket_type: str = Field(..., description="桶类型")
    policy: str = Field(default="private", description="访问策略")
    versioning_enabled: bool = Field(default=True, description="是否启用版本控制")
    lifecycle_enabled: bool = Field(default=False, description="是否启用生命周期管理")
    encryption_enabled: bool = Field(default=False, description="是否启用加密")
    cors_enabled: bool = Field(default=False, description="是否启用CORS")
    public_read: bool = Field(default=False, description="是否公开读取")

    @validator("bucket_type")
    def validate_bucket_type(cls, v: str) -> str:
        """Validate bucket type."""
        allowed_types = {"skills", "cache", "archives", "temp"}
        if v not in allowed_types:
            raise ValueError(f"Bucket type must be one of {allowed_types}")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BucketCreateRequest(BaseModel):
    """Request model for creating buckets."""

    config: BucketConfig = Field(..., description="桶配置")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BucketResponse(BaseModel):
    """Response model for bucket operations."""

    success: bool = Field(..., description="操作是否成功")
    bucket_name: Optional[str] = Field(None, description="桶名")
    message: Optional[str] = Field(None, description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
