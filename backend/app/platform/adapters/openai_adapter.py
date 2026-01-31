"""OpenAI platform adapter for skill deployment and management.

This module provides OpenAIAdapter class that implements platform-specific
logic for OpenAI's API integration, Functions format conversion, and deployment.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .base import (
    PlatformAdapter,
    PlatformCapability,
    ValidationError,
    ConfigurationError,
    DeploymentError,
    PlatformError,
)

logger = logging.getLogger(__name__)


class OpenAIAdapter(PlatformAdapter):
    """OpenAI platform adapter for skill deployment and management.

    Provides OpenAI-specific implementation including:
    - OpenAI API integration
    - Functions format conversion
    - ChatGPT model support
    - Token-based rate limiting
    """

    # Platform information
    platform_id = "openai"
    display_name = "OpenAI"
    platform_type = "llm_api"
    adapter_version = "1.0.0"
    platform_version = "2023-06-01"

    # Supported formats
    supported_formats = ["json", "yaml", "functions", "openai"]

    # Features
    features = [
        "streaming",
        "function_calling",
        "vision",
        "fine_tuning",
        "batch_operations",
        "multi_turn"
    ]

    # Capabilities
    capabilities = {
        PlatformCapability.FORMAT_CONVERSION: True,
        PlatformCapability.DEPLOYMENT: True,
        PlatformCapability.VALIDATION: True,
        PlatformCapability.STATUS_TRACKING: True,
        PlatformCapability.BULK_OPERATIONS: True,
        PlatformCapability.STREAMING: True,
        PlatformCapability.VISION: True,
        PlatformCapability.FUNCTION_CALLING: True,
    }

    # File size limits
    max_file_size = 50 * 1024 * 1024  # 50MB (OpenAI limit)
    format_size_limits = {
        "json": 30 * 1024 * 1024,  # 30MB
        "yaml": 30 * 1024 * 1024,  # 30MB
        "functions": 50 * 1024 * 1024,  # 50MB
        "openai": 50 * 1024 * 1024,  # 50MB
    }

    # Rate limits (requests per minute)
    rate_limits = {
        "requests_per_minute": 3000,
        "tokens_per_minute": 100000,
        "batch_size": 100
    }

    # OpenAI models
    supported_models = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4o-mini",
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI adapter.

        Args:
            config: Adapter configuration
        """
        super().__init__(config)

        # OpenAI-specific configuration
        self.api_key = self.config.get("api_key")
        self.organization_id = self.config.get("organization_id")
        self.base_url = self.config.get("base_url", "https://api.openai.com/v1")
        self.api_version = self.config.get("api_version", "2023-06-01")
        self.default_model = self.config.get("default_model", "gpt-3.5-turbo")
        self.timeout = self.config.get("timeout", 30)

        # Client session
        self._session = None

        # Rate limiting
        self._rate_limit_bucket = {
            "requests": self.rate_limits["requests_per_minute"],
            "tokens": self.rate_limits["tokens_per_minute"]
        }

    async def initialize(self) -> bool:
        """Initialize the OpenAI adapter.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Validate configuration
            if not await self.validate_configuration():
                return False

            # Initialize HTTP session
            await self._init_session()

            # Test API connection
            if not await self._test_connection():
                raise ConfigurationError(
                    "Failed to connect to OpenAI API",
                    platform=self.platform_id
                )

            self.is_initialized = True
            logger.info(f"OpenAI adapter initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI adapter: {str(e)}")
            self.is_initialized = False
            return False

    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate OpenAI adapter configuration.

        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []

        # Check required configuration
        if not self.api_key:
            errors.append("OpenAI API key is required")

        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            errors.append("Timeout must be a positive number")

        # Validate base URL
        if not self.base_url.startswith(("http://", "https://")):
            errors.append("Base URL must be a valid HTTP(S) URL")

        # Check optional configuration
        if not self.organization_id:
            warnings.append("Organization ID not provided (optional)")

        if not self.default_model or self.default_model not in self.supported_models:
            warnings.append(f"Default model '{self.default_model}' may not be supported")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on OpenAI platform.

        Returns:
            Health check result
        """
        try:
            if not self.is_initialized:
                return {
                    "healthy": False,
                    "message": "Adapter not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Test API availability
            response = await self._make_request(
                "GET",
                "/models",
                params={"limit": 1}
            )

            return {
                "healthy": response is not None,
                "message": "OpenAI API is accessible" if response else "API check failed",
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": getattr(response, "elapsed", 0)
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "message": f"Health check error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def validate_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate skill for OpenAI platform.

        Args:
            skill_data: Skill data to validate

        Returns:
            Validation result
        """
        errors = []
        warnings = []

        try:
            # Validate structure
            if not skill_data or not isinstance(skill_data, dict):
                errors.append("Skill data must be a non-empty dictionary")
                return {"valid": False, "errors": errors, "warnings": warnings}

            # Validate name
            if "name" not in skill_data:
                errors.append("Skill name is required")
            elif not skill_data["name"].strip():
                errors.append("Skill name cannot be empty")

            # Validate description
            if "description" not in skill_data:
                warnings.append("Skill description is recommended")
            elif len(skill_data["description"]) > 500:
                warnings.append("Description exceeds 500 characters (OpenAI best practice)")

            # Validate format-specific requirements
            format_type = skill_data.get("format", "json")
            await self._validate_format_specific(skill_data, format_type, errors, warnings)

            # Validate OpenAI Functions format
            if format_type in ["functions", "openai"]:
                await self._validate_functions_format(skill_data, errors, warnings)

            # Check file size
            data_str = json.dumps(skill_data, separators=(',', ':'))
            data_size = len(data_str.encode('utf-8'))

            if data_size > self.max_file_size:
                errors.append(f"Skill data exceeds maximum size of {self.max_file_size} bytes")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "format": format_type,
                "size_bytes": data_size
            }

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": warnings
            }

    async def validate_skill_format(self, skill_data: Dict[str, Any], format_type: str) -> Dict[str, Any]:
        """Validate skill format for OpenAI.

        Args:
            skill_data: Skill data
            format_type: Format type to validate

        Returns:
            Format validation result
        """
        errors = []
        warnings = []

        try:
            # Check supported formats
            if format_type not in self.supported_formats:
                errors.append(f"Unsupported format: {format_type}")
                return {"valid": False, "errors": errors, "warnings": warnings}

            # Format-specific validation
            if format_type == "functions":
                await self._validate_functions_format(skill_data, errors, warnings)
            elif format_type in ["json", "yaml"]:
                await self._validate_standard_format(skill_data, errors, warnings)
            elif format_type == "openai":
                await self._validate_openai_format(skill_data, errors, warnings)

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "format": format_type
            }

        except Exception as e:
            logger.error(f"Format validation error: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Format validation failed: {str(e)}"],
                "warnings": warnings
            }

    async def validate_skill_size(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate skill size for OpenAI.

        Args:
            skill_data: Skill data

        Returns:
            Size validation result
        """
        data_str = json.dumps(skill_data, separators=(',', ':'))
        data_size = len(data_str.encode('utf-8'))

        format_type = skill_data.get("format", "json")
        max_size = self.format_size_limits.get(format_type, self.max_file_size)

        return {
            "valid": data_size <= max_size,
            "size_bytes": data_size,
            "max_size_bytes": max_size,
            "format": format_type
        }

    async def convert_skill(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str
    ) -> Dict[str, Any]:
        """Convert skill to OpenAI format.

        Args:
            skill_data: Source skill data
            source_format: Source format
            target_format: Target format (openai or functions)

        Returns:
            Converted skill data
        """
        try:
            if target_format not in ["openai", "functions"]:
                raise ValidationError(
                    f"Unsupported target format: {target_format}",
                    platform=self.platform_id
                )

            # Get conversion template
            template = self.get_conversion_template(source_format, target_format)
            if not template:
                raise ValidationError(
                    f"No conversion template found from {source_format} to {target_format}",
                    platform=self.platform_id
                )

            # Perform conversion
            converted = await self._apply_conversion_template(skill_data, template)

            logger.info(f"Converted skill from {source_format} to {target_format}")
            return converted

        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            raise DeploymentError(
                f"Failed to convert skill: {str(e)}",
                platform=self.platform_id,
                details={"error": str(e)}
            )

    async def convert_from_platform(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert from OpenAI format to standard format.

        Args:
            platform_data: OpenAI format data

        Returns:
            Standard format data
        """
        try:
            # Detect format type
            if "functions" in platform_data or "tools" in platform_data:
                return await self._convert_from_functions_format(platform_data)
            else:
                return await self._convert_from_openai_format(platform_data)

        except Exception as e:
            logger.error(f"Platform conversion error: {str(e)}")
            raise ValidationError(
                f"Failed to convert from OpenAI format: {str(e)}",
                platform=self.platform_id
            )

    async def get_conversion_template(
        self,
        source_format: str,
        target_format: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversion template for formats.

        Args:
            source_format: Source format
            target_format: Target format

        Returns:
            Conversion template or None
        """
        templates = {
            ("json", "functions"): {
                "name": "name",
                "description": "description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "description": "Input parameters",
                            "type": "object"
                        }
                    }
                }
            },
            ("json", "openai"): {
                "name": "name",
                "description": "description",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            ("yaml", "functions"): {
                "name": "name",
                "description": "description",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            ("functions", "json"): {
                "name": "name",
                "description": "description",
                "type": "json"
            },
            ("openai", "json"): {
                "name": "name",
                "description": "description",
                "type": "openai"
            }
        }

        return templates.get((source_format, target_format))

    async def deploy_skill(
        self,
        skill_data: Dict[str, Any],
        deployment_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Deploy skill to OpenAI platform.

        Args:
            skill_data: Skill data to deploy
            deployment_config: Deployment configuration

        Returns:
            Deployment result
        """
        try:
            # Generate deployment ID
            deployment_id = str(uuid4())

            # Validate skill
            validation_result = await self.validate_skill(skill_data)
            if not validation_result["valid"]:
                raise ValidationError(
                    f"Skill validation failed: {validation_result['errors']}",
                    platform=self.platform_id
                )

            # Prepare deployment
            logger.info(f"Starting deployment for skill: {skill_data.get('name')}")

            # Convert to OpenAI format if needed
            format_type = skill_data.get("format", "json")
            if format_type not in ["functions", "openai"]:
                skill_data = await self.convert_skill(
                    skill_data,
                    format_type,
                    "functions"
                )

            # Deploy based on format
            if "functions" in skill_data:
                result = await self._deploy_functions(skill_data, deployment_id, deployment_config)
            else:
                result = await self._deploy_standard(skill_data, deployment_id, deployment_config)

            logger.info(f"Deployment completed: {deployment_id}")
            return result

        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            raise DeploymentError(
                f"Failed to deploy skill: {str(e)}",
                platform=self.platform_id,
                details={"error": str(e)}
            )

    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status from OpenAI.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status
        """
        try:
            # Query OpenAI for deployment status
            # Note: In real implementation, this would call OpenAI API
            # For now, return mock status
            return {
                "deployment_id": deployment_id,
                "status": "success",
                "platform": self.platform_id,
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "model": self.default_model,
                    "version": "v1"
                }
            }

        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            raise PlatformError(
                f"Failed to get deployment status: {str(e)}",
                platform=self.platform_id
            )

    async def cancel_deployment(self, deployment_id: str) -> bool:
        """Cancel deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            True if cancellation successful
        """
        try:
            # Cancel deployment via API
            # Note: In real implementation, this would call OpenAI API
            logger.info(f"Cancelled deployment: {deployment_id}")
            return True

        except Exception as e:
            logger.error(f"Cancellation error: {str(e)}")
            raise PlatformError(
                f"Failed to cancel deployment: {str(e)}",
                platform=self.platform_id
            )

    async def retry_deployment(
        self,
        deployment_id: str,
        skill_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Retry deployment.

        Args:
            deployment_id: Original deployment ID
            skill_data: Optional skill data to retry with

        Returns:
            Retry result
        """
        try:
            # Cancel original deployment
            await self.cancel_deployment(deployment_id)

            # Deploy again
            if skill_data:
                result = await self.deploy_skill(skill_data)
            else:
                # Get original skill data
                # Note: In real implementation, would retrieve from database
                raise ValidationError(
                    "Original skill data not available for retry",
                    platform=self.platform_id
                )

            return result

        except Exception as e:
            logger.error(f"Retry error: {str(e)}")
            raise DeploymentError(
                f"Failed to retry deployment: {str(e)}",
                platform=self.platform_id
            )

    async def get_platform_info(self) -> Dict[str, Any]:
        """Get OpenAI platform information.

        Returns:
            Platform information
        """
        return {
            "platform_id": self.platform_id,
            "display_name": self.display_name,
            "platform_type": self.platform_type,
            "api_endpoint": self.base_url,
            "api_version": self.api_version,
            "supported_models": self.supported_models,
            "supported_formats": self.supported_formats,
            "features": self.features,
            "capabilities": [c.value for c in self.capabilities.keys()],
            "rate_limits": self.rate_limits,
            "max_file_size": self.max_file_size,
            "format_size_limits": self.format_size_limits,
            "adapter_version": self.adapter_version,
            "platform_version": self.platform_version,
            "is_initialized": self.is_initialized
        }

    async def get_supported_models(self) -> List[str]:
        """Get list of supported models.

        Returns:
            List of model names
        """
        return self.supported_models.copy()

    async def get_api_limits(self) -> Dict[str, Any]:
        """Get API rate limits.

        Returns:
            Rate limit information
        """
        return self.rate_limits.copy()

    async def cleanup(self) -> None:
        """Cleanup adapter resources."""
        try:
            if self._session:
                await self._session.close()
                self._session = None

            self.is_initialized = False
            logger.info("OpenAI adapter cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

    # Private methods

    async def _init_session(self) -> None:
        """Initialize HTTP session."""
        import aiohttp

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"OpenAI-Adapter/{self.adapter_version}"
        }

        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id

        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )

    async def _test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection successful
        """
        try:
            response = await self._make_request("GET", "/models")
            return response is not None
        except Exception:
            return False

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Make API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters

        Returns:
            Response data or None
        """
        if not self._session:
            await self._init_session()

        url = f"{self.base_url}{endpoint}"

        try:
            async with self._session.request(
                method,
                url,
                json=data,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    logger.warning("Rate limit exceeded")
                    await asyncio.sleep(1)  # Backoff
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None

    async def _validate_format_specific(
        self,
        skill_data: Dict[str, Any],
        format_type: str,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate format-specific requirements.

        Args:
            skill_data: Skill data
            format_type: Format type
            errors: Error list
            warnings: Warning list
        """
        if format_type not in self.supported_formats:
            errors.append(f"Unsupported format: {format_type}")

    async def _validate_functions_format(
        self,
        skill_data: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate OpenAI Functions format.

        Args:
            skill_data: Skill data
            errors: Error list
            warnings: Warning list
        """
        # Check for functions structure
        if "functions" in skill_data:
            if not isinstance(skill_data["functions"], list):
                errors.append("Functions must be a list")
            else:
                for func in skill_data["functions"]:
                    if "name" not in func:
                        errors.append("Function name is required")
                    if "description" not in func:
                        warnings.append("Function description is recommended")
                    if "parameters" not in func:
                        errors.append("Function parameters are required")
                    elif not isinstance(func["parameters"], dict):
                        errors.append("Function parameters must be an object")

    async def _validate_standard_format(
        self,
        skill_data: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate standard JSON/YAML format.

        Args:
            skill_data: Skill data
            errors: Error list
            warnings: Warning list
        """
        # Standard validation already done in validate_skill
        pass

    async def _validate_openai_format(
        self,
        skill_data: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate OpenAI-specific format.

        Args:
            skill_data: Skill data
            errors: Error list
            warnings: Warning list
        """
        # Similar to functions validation
        await self._validate_functions_format(skill_data, errors, warnings)

    async def _apply_conversion_template(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply conversion template to skill data.

        Args:
            skill_data: Source skill data
            template: Conversion template

        Returns:
            Converted data
        """
        converted = {}

        # Map fields according to template
        for target_field, source_field in template.items():
            if isinstance(source_field, str):
                if source_field in skill_data:
                    converted[target_field] = skill_data[source_field]
            elif isinstance(source_field, dict):
                converted[target_field] = {}
                for sub_target, sub_source in source_field.items():
                    if sub_source in skill_data:
                        converted[target_field][sub_target] = skill_data[sub_source]

        # Add OpenAI-specific fields
        converted["type"] = "function"

        return converted

    async def _convert_from_functions_format(
        self,
        platform_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert from Functions format.

        Args:
            platform_data: Platform data

        Returns:
            Standard format data
        """
        # Extract standard fields
        converted = {
            "name": platform_data.get("name", ""),
            "description": platform_data.get("description", ""),
            "format": "functions"
        }

        return converted

    async def _convert_from_openai_format(
        self,
        platform_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert from OpenAI format.

        Args:
            platform_data: Platform data

        Returns:
            Standard format data
        """
        # Similar to functions conversion
        return await self._convert_from_functions_format(platform_data)

    async def _deploy_functions(
        self,
        skill_data: Dict[str, Any],
        deployment_id: str,
        deployment_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Deploy Functions format.

        Args:
            skill_data: Skill data
            deployment_id: Deployment ID
            deployment_config: Deployment config

        Returns:
            Deployment result
        """
        # In real implementation, this would call OpenAI Functions API
        return {
            "deployment_id": deployment_id,
            "status": "success",
            "platform": self.platform_id,
            "model": self.default_model,
            "timestamp": datetime.utcnow().isoformat(),
            "format": "functions"
        }

    async def _deploy_standard(
        self,
        skill_data: Dict[str, Any],
        deployment_id: str,
        deployment_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Deploy standard format.

        Args:
            skill_data: Skill data
            deployment_id: Deployment ID
            deployment_config: Deployment config

        Returns:
            Deployment result
        """
        # In real implementation, this would use OpenAI Chat API
        return {
            "deployment_id": deployment_id,
            "status": "success",
            "platform": self.platform_id,
            "model": self.default_model,
            "timestamp": datetime.utcnow().isoformat(),
            "format": "standard"
        }

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle OpenAI-specific errors.

        Args:
            error: Exception to handle

        Returns:
            Error information
        """
        error_info = {
            "error": str(error),
            "error_type": type(error).__name__,
            "platform": self.platform_id
        }

        # Add OpenAI-specific error details
        if hasattr(error, "status_code"):
            error_info["status_code"] = error.status_code

        if hasattr(error, "response"):
            error_info["response"] = str(error.response)

        return error_info

    def is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error is retryable
        """
        # OpenAI retryable errors
        retryable_errors = (
            "RateLimitError",
            "Timeout",
            "ConnectionError",
            "TemporaryFailure"
        )

        return any(err_name in str(error) for err_name in retryable_errors)