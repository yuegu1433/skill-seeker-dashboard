"""Base platform adapter interface.

This module defines the abstract base class for all platform adapters,
providing a unified interface for platform-specific operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PlatformAdapter(ABC):
    """Abstract base class for platform adapters.

    This class defines the standard interface that all platform adapters must implement,
    ensuring consistent behavior across different LLM platforms.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the platform adapter.

        Args:
            config: Platform-specific configuration dictionary
        """
        self.config = config or {}
        self.platform_name = self.__class__.__name__.replace('Adapter', '').lower()
        self.is_initialized = False

    # Platform Information Methods
    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Get unique platform identifier.

        Returns:
            Platform identifier string
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get human-readable platform name.

        Returns:
            Display name string
        """
        pass

    @property
    @abstractmethod
    def platform_type(self) -> str:
        """Get platform type identifier.

        Returns:
            Platform type string (e.g., 'claude', 'gemini', 'openai', 'markdown')
        """
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Get list of supported skill formats.

        Returns:
            List of supported format identifiers
        """
        pass

    @property
    @abstractmethod
    def max_file_size(self) -> int:
        """Get maximum supported file size in bytes.

        Returns:
            Maximum file size in bytes
        """
        pass

    @property
    @abstractmethod
    def features(self) -> Dict[str, Any]:
        """Get platform-specific features and capabilities.

        Returns:
            Dictionary of platform features
        """
        pass

    # Initialization Methods
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the platform adapter.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate platform configuration.

        Returns:
            Validation result dictionary with 'valid' key and 'errors' list
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform platform health check.

        Returns:
            Health check result dictionary with status and details
        """
        pass

    # Skill Validation Methods
    @abstractmethod
    async def validate_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate skill for platform compatibility.

        Args:
            skill_data: Skill data to validate

        Returns:
            Validation result with 'valid', 'errors', and 'warnings' keys
        """
        pass

    @abstractmethod
    async def validate_skill_format(self, skill_format: str) -> bool:
        """Check if skill format is supported.

        Args:
            skill_format: Format identifier to check

        Returns:
            True if format is supported, False otherwise
        """
        pass

    @abstractmethod
    async def validate_skill_size(self, skill_size: int) -> bool:
        """Check if skill size is within platform limits.

        Args:
            skill_size: Skill size in bytes

        Returns:
            True if size is acceptable, False otherwise
        """
        pass

    # Format Conversion Methods
    @abstractmethod
    async def convert_skill(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert skill to platform-specific format.

        Args:
            skill_data: Source skill data
            source_format: Source format identifier
            target_format: Target format identifier (optional, defaults to platform format)

        Returns:
            Converted skill data in platform format
        """
        pass

    @abstractmethod
    async def convert_from_platform(
        self,
        skill_data: Dict[str, Any],
        target_format: str
    ) -> Dict[str, Any]:
        """Convert skill from platform format to target format.

        Args:
            skill_data: Platform-specific skill data
            target_format: Target format identifier

        Returns:
            Converted skill data in target format
        """
        pass

    @abstractmethod
    async def get_conversion_template(
        self,
        source_format: str,
        target_format: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversion template for format transformation.

        Args:
            source_format: Source format identifier
            target_format: Target format identifier

        Returns:
            Conversion template dictionary or None if not available
        """
        pass

    # Deployment Methods
    @abstractmethod
    async def deploy_skill(
        self,
        skill_data: Dict[str, Any],
        deployment_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Deploy skill to platform.

        Args:
            skill_data: Skill data to deploy
            deployment_config: Deployment configuration

        Returns:
            Deployment result with status and deployment details
        """
        pass

    @abstractmethod
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status.

        Args:
            deployment_id: Platform-specific deployment identifier

        Returns:
            Deployment status information
        """
        pass

    @abstractmethod
    async def cancel_deployment(self, deployment_id: str) -> bool:
        """Cancel ongoing deployment.

        Args:
            deployment_id: Platform-specific deployment identifier

        Returns:
            True if cancellation successful, False otherwise
        """
        pass

    @abstractmethod
    async def retry_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Retry failed deployment.

        Args:
            deployment_id: Platform-specific deployment identifier

        Returns:
            Retry result with new deployment details
        """
        pass

    # Platform-Specific Methods
    @abstractmethod
    async def get_platform_info(self) -> Dict[str, Any]:
        """Get detailed platform information.

        Returns:
            Comprehensive platform information
        """
        pass

    @abstractmethod
    async def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported models.

        Returns:
            List of model information dictionaries
        """
        pass

    @abstractmethod
    async def get_api_limits(self) -> Dict[str, Any]:
        """Get platform API rate limits and quotas.

        Returns:
            API limits and quotas information
        """
        pass

    # Error Handling Methods
    @abstractmethod
    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle and categorize platform errors.

        Args:
            error: Exception to handle

        Returns:
            Error information dictionary with categorization
        """
        pass

    @abstractmethod
    def is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error is retryable, False otherwise
        """
        pass

    # Cleanup Methods
    async def cleanup(self) -> None:
        """Cleanup resources and connections."""
        self.is_initialized = False
        logger.info(f"Cleaned up adapter for platform: {self.platform_name}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    # Utility Methods
    def __repr__(self) -> str:
        """Return string representation."""
        return f"<{self.__class__.__name__}(platform={self.platform_name})>"

    def get_platform_summary(self) -> Dict[str, Any]:
        """Get platform summary information.

        Returns:
            Platform summary dictionary
        """
        return {
            'platform_id': self.platform_id,
            'display_name': self.display_name,
            'platform_type': self.platform_type,
            'supported_formats': self.supported_formats,
            'max_file_size': self.max_file_size,
            'features': self.features,
            'is_initialized': self.is_initialized,
        }

    def supports_format(self, format_name: str) -> bool:
        """Check if platform supports a specific format.

        Args:
            format_name: Format identifier to check

        Returns:
            True if format is supported
        """
        return format_name in self.supported_formats

    def can_handle_skill_size(self, skill_size: int) -> bool:
        """Check if platform can handle skill size.

        Args:
            skill_size: Skill size in bytes

        Returns:
            True if size is within limits
        """
        return skill_size <= self.max_file_size

    def get_max_size_for_format(self, format_name: str) -> int:
        """Get maximum file size for a specific format.

        Args:
            format_name: Format identifier

        Returns:
            Maximum file size in bytes for the format
        """
        # Default implementation returns platform max size
        # Subclasses can override for format-specific limits
        format_limits = self.features.get('format_limits', {})
        return format_limits.get(format_name, self.max_file_size)

    # Version Information
    @property
    def adapter_version(self) -> str:
        """Get adapter version.

        Returns:
            Adapter version string
        """
        return "1.0.0"

    @property
    def platform_version(self) -> Optional[str]:
        """Get platform API version.

        Returns:
            Platform version string or None
        """
        return self.config.get('api_version')

    # Capabilities
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get platform capabilities.

        Returns:
            Dictionary of capability flags
        """
        return {
            'validation': True,
            'conversion': True,
            'deployment': True,
            'monitoring': True,
            'batch_operations': self.features.get('batch_operations', False),
            'streaming': self.features.get('streaming', False),
            'multimodal': self.features.get('multimodal', False),
        }

    def has_capability(self, capability: str) -> bool:
        """Check if platform has specific capability.

        Args:
            capability: Capability identifier

        Returns:
            True if capability is supported
        """
        return self.capabilities.get(capability, False)


class PlatformCapability:
    """Platform capability constants."""
    VALIDATION = "validation"
    CONVERSION = "conversion"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    BATCH_OPERATIONS = "batch_operations"
    STREAMING = "streaming"
    MULTIMODAL = "multimodal"


class PlatformError(Exception):
    """Base exception for platform adapter errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        platform: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize platform error.

        Args:
            message: Error message
            error_code: Optional error code
            platform: Optional platform identifier
            details: Optional error details
        """
        super().__init__(message)
        self.error_code = error_code
        self.platform = platform
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class ValidationError(PlatformError):
    """Raised when skill validation fails."""
    pass


class ConversionError(PlatformError):
    """Raised when format conversion fails."""
    pass


class DeploymentError(PlatformError):
    """Raised when deployment fails."""
    pass


class ConfigurationError(PlatformError):
    """Raised when platform configuration is invalid."""
    pass


class RateLimitError(PlatformError):
    """Raised when API rate limit is exceeded."""
    pass


class UnsupportedFormatError(PlatformError):
    """Raised when format is not supported."""
    pass


class FileSizeError(PlatformError):
    """Raised when file size exceeds limits."""
    pass