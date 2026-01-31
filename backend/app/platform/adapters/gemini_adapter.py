"""Gemini platform adapter.

This module implements the PlatformAdapter for Google's Gemini platform,
providing Gemini-specific integration for skill validation, conversion, and deployment.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import (
    PlatformAdapter,
    ValidationError,
    ConversionError,
    DeploymentError,
    ConfigurationError,
    RateLimitError,
    UnsupportedFormatError,
    FileSizeError,
)

logger = logging.getLogger(__name__)


class GeminiAdapter(PlatformAdapter):
    """Platform adapter for Google's Gemini platform.

    Provides Gemini-specific implementation of platform adapter methods,
    including API integration, skill validation, format conversion, and deployment.
    """

    # Platform Information
    @property
    def platform_id(self) -> str:
        """Get unique platform identifier."""
        return "gemini"

    @property
    def display_name(self) -> str:
        """Get human-readable platform name."""
        return "Google Gemini"

    @property
    def platform_type(self) -> str:
        """Get platform type identifier."""
        return "gemini"

    @property
    def supported_formats(self) -> List[str]:
        """Get list of supported skill formats."""
        return ["gemini", "json", "yaml", "markdown", "protobuf"]

    @property
    def max_file_size(self) -> int:
        """Get maximum supported file size in bytes."""
        return 150 * 1024 * 1024  # 150MB

    @property
    def features(self) -> Dict[str, Any]:
        """Get platform-specific features and capabilities."""
        return {
            "supports_multimodal": True,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_code_execution": True,
            "max_tokens": 32768,
            "supported_models": [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-pro",
                "gemini-pro-vision",
            ],
            "rate_limits": {
                "requests_per_minute": 60,
                "tokens_per_minute": 100000,
            },
            "batch_operations": True,
            "streaming": True,
            "multimodal": True,
            "code_execution": True,
            "format_limits": {
                "json": 75 * 1024 * 1024,  # 75MB
                "yaml": 75 * 1024 * 1024,  # 75MB
                "markdown": 150 * 1024 * 1024,  # 150MB
                "protobuf": 150 * 1024 * 1024,  # 150MB
            },
        }

    # Initialization Methods
    async def initialize(self) -> bool:
        """Initialize the Gemini adapter.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Validate configuration
            validation_result = await self.validate_configuration()
            if not validation_result.get("valid", False):
                logger.error(f"Configuration validation failed: {validation_result.get('errors')}")
                return False

            # Perform health check
            health_result = await self.health_check()
            if health_result.get("status") != "healthy":
                logger.error(f"Health check failed: {health_result}")
                return False

            self.is_initialized = True
            logger.info("Gemini adapter initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Gemini adapter: {str(e)}")
            return False

    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate platform configuration.

        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []

        # Check required configuration
        required_fields = ["api_key"]
        for field in required_fields:
            if field not in self.config:
                errors.append(f"Missing required configuration: {field}")

        # Check optional configurations
        if "api_version" in self.config:
            valid_versions = ["v1", "v1beta"]
            if self.config["api_version"] not in valid_versions:
                warnings.append(f"API version may not be supported: {self.config['api_version']}")

        # Validate API key format if present
        if "api_key" in self.config:
            api_key = self.config["api_key"]
            if not isinstance(api_key, str) or len(api_key) < 10:
                errors.append("Invalid API key format")

        # Validate project ID if present
        if "project_id" in self.config:
            project_id = self.config["project_id"]
            if not isinstance(project_id, str) or len(project_id) < 3:
                warnings.append("Project ID format may be invalid")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform platform health check.

        Returns:
            Health check result dictionary
        """
        try:
            start_time = datetime.utcnow()

            # Simulate API call to check connectivity
            # In real implementation, this would make actual API call to Gemini
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "api_accessible": True,
                    "authentication_valid": True,
                    "rate_limits_normal": True,
                    "multimodal_enabled": True,
                }
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # Skill Validation Methods
    async def validate_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate skill for platform compatibility.

        Args:
            skill_data: Skill data to validate

        Returns:
            Validation result with 'valid', 'errors', and 'warnings' keys
        """
        errors = []
        warnings = []

        try:
            # Check required fields
            required_fields = ["name", "description", "instructions"]
            for field in required_fields:
                if field not in skill_data:
                    errors.append(f"Missing required field: {field}")

            # Check format compatibility
            skill_format = skill_data.get("format", "json")
            if not self.validate_skill_format(skill_format):
                errors.append(f"Unsupported skill format: {skill_format}")

            # Check file size
            skill_size = skill_data.get("size", 0)
            if not self.validate_skill_size(skill_size):
                errors.append(f"Skill size exceeds platform limit: {skill_size} bytes")

            # Validate Gemini-specific requirements
            if "instructions" in skill_data:
                instructions = skill_data["instructions"]
                if isinstance(instructions, str) and len(instructions) > 100000:
                    warnings.append("Instructions are very long, may impact performance")

            # Check for supported features
            unsupported_features = []
            if skill_data.get("requires_file_system", False):
                warnings.append("Gemini has limited file system access")

            # Check for multimodal requirements
            if skill_data.get("multimodal", False):
                if not self.features.get("multimodal", False):
                    errors.append("Multimodal features not enabled for this configuration")

            # Validate model compatibility
            if "model" in skill_data:
                supported_models = self.features["supported_models"]
                if skill_data["model"] not in supported_models:
                    warnings.append(f"Model may not be supported: {skill_data['model']}")

            # Check for code execution compatibility
            if skill_data.get("supports_code_execution", False):
                if not self.features.get("supports_code_execution", False):
                    warnings.append("Code execution may not be fully supported")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
            }

        except Exception as e:
            logger.error(f"Skill validation error: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": warnings,
            }

    async def validate_skill_format(self, skill_format: str) -> bool:
        """Check if skill format is supported.

        Args:
            skill_format: Format identifier to check

        Returns:
            True if format is supported, False otherwise
        """
        return skill_format in self.supported_formats

    async def validate_skill_size(self, skill_size: int) -> bool:
        """Check if skill size is within platform limits.

        Args:
            skill_size: Skill size in bytes

        Returns:
            True if size is acceptable, False otherwise
        """
        format_limits = self.features.get("format_limits", {})
        format_specific_limit = format_limits.get("unknown", self.max_file_size)

        # Use format-specific limit if available, otherwise use general limit
        limit = format_specific_limit

        return skill_size <= limit

    # Format Conversion Methods
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
            target_format: Target format identifier

        Returns:
            Converted skill data in platform format
        """
        try:
            if target_format is None:
                target_format = "gemini"

            # Get conversion template
            template = await self.get_conversion_template(source_format, target_format)
            if not template:
                raise ConversionError(
                    f"No conversion template found for {source_format} to {target_format}",
                    platform=self.platform_id
                )

            # Apply conversion based on source format
            if source_format == "json":
                converted_data = await self._convert_from_json(skill_data, template)
            elif source_format == "yaml":
                converted_data = await self._convert_from_yaml(skill_data, template)
            elif source_format == "markdown":
                converted_data = await self._convert_from_markdown(skill_data, template)
            elif source_format == "protobuf":
                converted_data = await self._convert_from_protobuf(skill_data, template)
            else:
                raise UnsupportedFormatError(
                    f"Unsupported source format: {source_format}",
                    platform=self.platform_id
                )

            # Add Gemini-specific metadata
            converted_data["platform"] = self.platform_id
            converted_data["converted_at"] = datetime.utcnow().isoformat()
            converted_data["conversion_template"] = template.get("name", "unknown")
            converted_data["supports_multimodal"] = True

            logger.info(f"Successfully converted skill from {source_format} to {target_format}")
            return converted_data

        except Exception as e:
            logger.error(f"Skill conversion failed: {str(e)}")
            raise ConversionError(
                f"Failed to convert skill: {str(e)}",
                platform=self.platform_id,
                details={"source_format": source_format, "target_format": target_format}
            )

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
        try:
            if target_format == "json":
                return await self._convert_to_json(skill_data)
            elif target_format == "yaml":
                return await self._convert_to_yaml(skill_data)
            elif target_format == "markdown":
                return await self._convert_to_markdown(skill_data)
            elif target_format == "protobuf":
                return await self._convert_to_protobuf(skill_data)
            else:
                raise UnsupportedFormatError(
                    f"Unsupported target format: {target_format}",
                    platform=self.platform_id
                )

        except Exception as e:
            logger.error(f"Platform conversion failed: {str(e)}")
            raise ConversionError(
                f"Failed to convert from platform format: {str(e)}",
                platform=self.platform_id,
                details={"target_format": target_format}
            )

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
        templates = {
            "json_to_gemini": {
                "name": "JSON to Gemini Format",
                "description": "Converts JSON skill format to Gemini-specific format",
                "field_mapping": {
                    "name": "displayName",
                    "description": "description",
                    "instructions": "instruction",
                    "examples": "examples",
                },
                "transformations": [
                    "extract_instructions",
                    "format_examples",
                    "add_multimodal_support",
                ],
            },
            "yaml_to_gemini": {
                "name": "YAML to Gemini Format",
                "description": "Converts YAML skill format to Gemini-specific format",
                "field_mapping": {
                    "name": "displayName",
                    "description": "description",
                    "instructions": "instruction",
                    "examples": "examples",
                },
                "transformations": [
                    "parse_yaml",
                    "extract_instructions",
                    "format_examples",
                ],
            },
            "markdown_to_gemini": {
                "name": "Markdown to Gemini Format",
                "description": "Converts Markdown skill format to Gemini-specific format",
                "field_mapping": {
                    "title": "displayName",
                    "content": "instruction",
                    "examples": "examples",
                },
                "transformations": [
                    "parse_markdown",
                    "extract_sections",
                    "format_instructions",
                ],
            },
            "protobuf_to_gemini": {
                "name": "Protobuf to Gemini Format",
                "description": "Converts Protobuf skill format to Gemini-specific format",
                "field_mapping": {
                    "name": "displayName",
                    "description": "description",
                    "instructions": "instruction",
                    "multimodal_data": "multimodalData",
                },
                "transformations": [
                    "parse_protobuf",
                    "extract_structured_data",
                    "validate_multimodal",
                ],
            },
        }

        template_key = f"{source_format}_to_{target_format}"
        return templates.get(template_key)

    # Deployment Methods
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
        try:
            deployment_config = deployment_config or {}

            # Validate skill before deployment
            validation_result = await self.validate_skill(skill_data)
            if not validation_result["valid"]:
                raise ValidationError(
                    f"Skill validation failed: {validation_result['errors']}",
                    platform=self.platform_id,
                    details=validation_result
                )

            # Prepare deployment payload
            deployment_payload = {
                "displayName": skill_data.get("name"),
                "description": skill_data.get("description"),
                "instruction": skill_data.get("instructions"),
                "examples": skill_data.get("examples", []),
                "metadata": {
                    "source_format": skill_data.get("format", "unknown"),
                    "deployed_at": datetime.utcnow().isoformat(),
                    "platform": self.platform_id,
                    "supports_multimodal": skill_data.get("multimodal", False),
                }
            }

            # Add deployment configuration
            if "model" in deployment_config:
                deployment_payload["model"] = deployment_config["model"]
            if "multimodal" in deployment_config:
                deployment_payload["supports_multimodal"] = deployment_config["multimodal"]

            # Simulate deployment API call
            deployment_id = f"gemini_deployment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # In real implementation, this would make actual API call to Gemini platform
            logger.info(f"Deploying skill to Gemini platform: {deployment_id}")

            return {
                "status": "success",
                "deployment_id": deployment_id,
                "platform": self.platform_id,
                "deployed_at": datetime.utcnow().isoformat(),
                "details": {
                    "model": deployment_config.get("model", "gemini-1.5-pro"),
                    "region": "us-central1",
                    "status": "active",
                    "supports_multimodal": deployment_config.get("multimodal", False),
                },
                "warnings": validation_result.get("warnings", []),
            }

        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise DeploymentError(
                f"Failed to deploy skill: {str(e)}",
                platform=self.platform_id,
                details={"skill_name": skill_data.get("name")}
            )

    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status.

        Args:
            deployment_id: Platform-specific deployment identifier

        Returns:
            Deployment status information
        """
        try:
            # In real implementation, this would query the Gemini API
            logger.info(f"Checking deployment status: {deployment_id}")

            return {
                "deployment_id": deployment_id,
                "status": "active",
                "platform": self.platform_id,
                "last_checked": datetime.utcnow().isoformat(),
                "details": {
                    "health": "healthy",
                    "uptime": "99.95%",
                    "last_deployment": datetime.utcnow().isoformat(),
                    "multimodal_enabled": True,
                }
            }

        except Exception as e:
            logger.error(f"Failed to get deployment status: {str(e)}")
            raise DeploymentError(
                f"Failed to get deployment status: {str(e)}",
                platform=self.platform_id,
                details={"deployment_id": deployment_id}
            )

    async def cancel_deployment(self, deployment_id: str) -> bool:
        """Cancel ongoing deployment.

        Args:
            deployment_id: Platform-specific deployment identifier

        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            logger.info(f"Cancelling deployment: {deployment_id}")
            # In real implementation, this would call Gemini API
            return True

        except Exception as e:
            logger.error(f"Failed to cancel deployment: {str(e)}")
            return False

    async def retry_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Retry failed deployment.

        Args:
            deployment_id: Platform-specific deployment identifier

        Returns:
            Retry result with new deployment details
        """
        try:
            logger.info(f"Retrying deployment: {deployment_id}")
            # In real implementation, this would retry via Gemini API

            new_deployment_id = f"gemini_deployment_retry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            return {
                "status": "success",
                "original_deployment_id": deployment_id,
                "new_deployment_id": new_deployment_id,
                "platform": self.platform_id,
                "retried_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to retry deployment: {str(e)}")
            raise DeploymentError(
                f"Failed to retry deployment: {str(e)}",
                platform=self.platform_id,
                details={"original_deployment_id": deployment_id}
            )

    # Platform-Specific Methods
    async def get_platform_info(self) -> Dict[str, Any]:
        """Get detailed platform information.

        Returns:
            Comprehensive platform information
        """
        return {
            "platform_id": self.platform_id,
            "display_name": self.display_name,
            "platform_type": self.platform_type,
            "api_version": self.config.get("api_version", "v1"),
            "supported_models": self.features["supported_models"],
            "capabilities": {
                "text_generation": True,
                "code_generation": True,
                "analysis": True,
                "reasoning": True,
                "multimodal": True,
                "function_calling": True,
                "code_execution": True,
            },
            "limitations": {
                "max_context_length": 32768,
                "max_output_tokens": 8192,
                "rate_limits": self.features["rate_limits"],
            },
            "documentation_url": "https://ai.google.dev/gemini-api",
            "api_reference_url": "https://ai.google.dev/api/rest",
        }

    async def get_supported_models(self) -> List[Dict[str, Any]]:
        """Get list of supported models.

        Returns:
            List of model information dictionaries
        """
        models = [
            {
                "id": "gemini-1.5-pro",
                "name": "Gemini 1.5 Pro",
                "description": "Most capable model for complex reasoning",
                "context_length": 32768,
                "max_output_tokens": 8192,
                "capabilities": ["text", "code", "multimodal", "reasoning"],
            },
            {
                "id": "gemini-1.5-flash",
                "name": "Gemini 1.5 Flash",
                "description": "Fast model for most tasks",
                "context_length": 32768,
                "max_output_tokens": 8192,
                "capabilities": ["text", "code", "multimodal"],
            },
            {
                "id": "gemini-pro",
                "name": "Gemini Pro",
                "description": "General purpose model",
                "context_length": 30720,
                "max_output_tokens": 2048,
                "capabilities": ["text", "code"],
            },
            {
                "id": "gemini-pro-vision",
                "name": "Gemini Pro Vision",
                "description": "Model with vision capabilities",
                "context_length": 12288,
                "max_output_tokens": 4096,
                "capabilities": ["text", "vision", "multimodal"],
            },
        ]

        return models

    async def get_api_limits(self) -> Dict[str, Any]:
        """Get platform API rate limits and quotas.

        Returns:
            API limits and quotas information
        """
        return {
            "rate_limits": self.features["rate_limits"],
            "quota_reset": "daily",
            "quota_usage": {
                "requests_today": 0,
                "tokens_today": 0,
            },
            "limits": {
                "requests_per_minute": 60,
                "tokens_per_minute": 100000,
                "requests_per_day": 1500,
                "tokens_per_day": 1000000,
            },
        }

    # Error Handling Methods
    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle and categorize platform errors.

        Args:
            error: Exception to handle

        Returns:
            Error information dictionary with categorization
        """
        error_info = {
            "error_type": type(error).__name__,
            "message": str(error),
            "platform": self.platform_id,
            "timestamp": datetime.utcnow().isoformat(),
            "retryable": False,
            "category": "unknown",
        }

        # Categorize error
        if isinstance(error, RateLimitError):
            error_info.update({
                "category": "rate_limit",
                "retryable": True,
                "retry_after": 60,
            })
        elif isinstance(error, ValidationError):
            error_info.update({
                "category": "validation",
                "retryable": False,
            })
        elif isinstance(error, ConfigurationError):
            error_info.update({
                "category": "configuration",
                "retryable": False,
            })
        elif isinstance(error, DeploymentError):
            error_info.update({
                "category": "deployment",
                "retryable": True,
            })

        logger.error(f"Handled {error_info['category']} error: {error_info['message']}")
        return error_info

    def is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error is retryable, False otherwise
        """
        retryable_errors = (
            RateLimitError,
            DeploymentError,
            ConnectionError,
            TimeoutError,
        )

        return isinstance(error, retryable_errors)

    # Private Helper Methods
    async def _convert_from_json(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert skill from JSON format."""
        # Apply field mapping from template
        field_mapping = template.get("field_mapping", {})
        converted = {}

        for source_field, target_field in field_mapping.items():
            if source_field in skill_data:
                converted[target_field] = skill_data[source_field]

        # Apply transformations
        for transformation in template.get("transformations", []):
            if transformation == "extract_instructions":
                if "instruction" in converted:
                    instruction = converted["instruction"]
                    if isinstance(instruction, dict):
                        converted["instruction"] = instruction.get("text", "")
            elif transformation == "format_examples":
                if "examples" in converted:
                    examples = converted["examples"]
                    if isinstance(examples, list):
                        converted["examples"] = examples
            elif transformation == "add_multimodal_support":
                converted["supports_multimodal"] = skill_data.get("multimodal", False)

        return converted

    async def _convert_from_yaml(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert skill from YAML format."""
        # YAML conversion would parse YAML and apply similar transformations
        # This is a simplified implementation
        return await self._convert_from_json(skill_data, template)

    async def _convert_from_markdown(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert skill from Markdown format."""
        # Markdown conversion would parse markdown and extract sections
        # This is a simplified implementation
        converted = {}

        # Extract title
        if "title" in skill_data:
            converted["displayName"] = skill_data["title"]

        # Extract content as instruction
        if "content" in skill_data:
            converted["instruction"] = skill_data["content"]

        # Extract examples from markdown sections
        if "sections" in skill_data:
            for section in skill_data["sections"]:
                if section.get("type") == "example":
                    if "examples" not in converted:
                        converted["examples"] = []
                    converted["examples"].append(section.get("content", ""))

        return converted

    async def _convert_from_protobuf(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert skill from Protobuf format."""
        # Protobuf conversion would parse Protobuf format
        # This is a simplified implementation
        converted = {}

        # Extract fields from Protobuf structure
        if "name" in skill_data:
            converted["displayName"] = skill_data["name"]
        if "description" in skill_data:
            converted["description"] = skill_data["description"]
        if "instruction" in skill_data:
            converted["instruction"] = skill_data["instruction"]
        if "multimodalData" in skill_data:
            converted["multimodalData"] = skill_data["multimodalData"]

        return converted

    async def _convert_to_json(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert skill to JSON format."""
        # Convert Gemini format back to JSON
        return {
            "format": "json",
            "name": skill_data.get("displayName"),
            "description": skill_data.get("description"),
            "instructions": skill_data.get("instruction"),
            "examples": skill_data.get("examples", []),
            "multimodal": skill_data.get("supports_multimodal", False),
            "metadata": skill_data.get("metadata", {}),
        }

    async def _convert_to_yaml(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert skill to YAML format."""
        # Convert to YAML-compatible format
        return {
            "format": "yaml",
            "name": skill_data.get("displayName"),
            "description": skill_data.get("description"),
            "instructions": skill_data.get("instruction"),
            "examples": skill_data.get("examples", []),
            "multimodal": skill_data.get("supports_multimodal", False),
        }

    async def _convert_to_markdown(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert skill to Markdown format."""
        # Convert to Markdown format
        markdown_content = []

        # Add title
        if "displayName" in skill_data:
            markdown_content.append(f"# {skill_data['displayName']}")

        # Add description
        if "description" in skill_data:
            markdown_content.append(f"\n{skill_data['description']}\n")

        # Add instruction
        if "instruction" in skill_data:
            markdown_content.append("## Instruction\n")
            markdown_content.append(f"{skill_data['instruction']}\n")

        # Add examples
        if "examples" in skill_data and skill_data["examples"]:
            markdown_content.append("## Examples\n")
            for example in skill_data["examples"]:
                markdown_content.append(f"- {example}\n")

        # Add multimodal info
        if skill_data.get("supports_multimodal"):
            markdown_content.append("\n## Multimodal Support\n")
            markdown_content.append("This skill supports multimodal inputs.\n")

        return {
            "format": "markdown",
            "title": skill_data.get("displayName"),
            "content": "\n".join(markdown_content),
        }

    async def _convert_to_protobuf(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert skill to Protobuf format."""
        # Convert to Protobuf-compatible format
        return {
            "format": "protobuf",
            "name": skill_data.get("displayName"),
            "description": skill_data.get("description"),
            "instruction": skill_data.get("instruction"),
            "examples": skill_data.get("examples", []),
            "multimodalData": {
                "supported": skill_data.get("supports_multimodal", False),
            },
        }