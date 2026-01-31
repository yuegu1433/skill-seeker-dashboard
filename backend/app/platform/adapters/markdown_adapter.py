"""Markdown platform adapter for skill documentation and file generation.

This module provides MarkdownAdapter class that implements platform-specific
logic for Markdown format conversion, documentation generation, and file operations.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from pathlib import Path

from .base import (
    PlatformAdapter,
    PlatformCapability,
    ValidationError,
    ConfigurationError,
    DeploymentError,
    PlatformError,
)

logger = logging.getLogger(__name__)


class MarkdownAdapter(PlatformAdapter):
    """Markdown platform adapter for documentation and file generation.

    Provides Markdown-specific implementation including:
    - Markdown format validation
    - Document generation
    - File output
    - Format conversion
    - Syntax highlighting
    """

    # Platform information
    platform_id = "markdown"
    display_name = "Markdown"
    platform_type = "document_format"
    adapter_version = "1.0.0"
    platform_version = "1.0"

    # Supported formats
    supported_formats = ["markdown", "md", "json", "yaml"]

    # Features
    features = [
        "document_generation",
        "syntax_highlighting",
        "table_support",
        "code_blocks",
        "math_support",
        "diagrams",
        "toc_generation",
        "frontmatter"
    ]

    # Capabilities
    capabilities = {
        PlatformCapability.FORMAT_CONVERSION: True,
        PlatformCapability.DEPLOYMENT: True,
        PlatformCapability.VALIDATION: True,
        PlatformCapability.STATUS_TRACKING: True,
        PlatformCapability.BULK_OPERATIONS: True,
        PlatformCapability.STREAMING: False,
        PlatformCapability.VISION: False,
        PlatformCapability.FUNCTION_CALLING: False,
    }

    # File size limits
    max_file_size = 100 * 1024 * 1024  # 100MB (largest limit)
    format_size_limits = {
        "markdown": 100 * 1024 * 1024,  # 100MB
        "md": 100 * 1024 * 1024,  # 100MB
        "json": 30 * 1024 * 1024,  # 30MB
        "yaml": 30 * 1024 * 1024,  # 30MB
    }

    # Markdown extensions
    supported_extensions = [
        "markdown",
        "extra",
        "codehilite",
        "toc",
        "tables",
        "fenced_code",
        "footnotes",
        "attr_list",
        "def_list",
        "abbr",
        "md_in_html"
    ]

    # Conversion templates
    conversion_templates = {}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Markdown adapter.

        Args:
            config: Adapter configuration
        """
        super().__init__(config)

        # Markdown-specific configuration
        self.output_directory = self.config.get("output_directory", "./output")
        self.encoding = self.config.get("encoding", "utf-8")
        self.line_ending = self.config.get("line_ending", "lf")  # lf, crlf, cr
        self.indent_size = self.config.get("indent_size", 2)
        self.wrap_width = self.config.get("wrap_width", 80)

        # Extensions configuration
        self.extensions = self.config.get("extensions", self.supported_extensions)
        self.toc_depth = self.config.get("toc_depth", 3)
        self.toc_permalink = self.config.get("toc_permalink", True)

        # Template configuration
        self.template_engine = self.config.get("template_engine", "jinja2")
        self.custom_templates = self.config.get("custom_templates", {})

        # Initialize output directory
        self._init_output_directory()

    async def initialize(self) -> bool:
        """Initialize the Markdown adapter.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Validate configuration
            if not await self.validate_configuration():
                return False

            # Create output directory
            Path(self.output_directory).mkdir(parents=True, exist_ok=True)

            # Test template engine
            if self.template_engine == "jinja2":
                await self._test_jinja2()

            self.is_initialized = True
            logger.info(f"Markdown adapter initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Markdown adapter: {str(e)}")
            self.is_initialized = False
            return False

    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate Markdown adapter configuration.

        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []

        # Validate output directory
        if not self.output_directory:
            errors.append("Output directory is required")
        elif not Path(self.output_directory).exists():
            warnings.append(f"Output directory does not exist: {self.output_directory}")

        # Validate encoding
        valid_encodings = ["utf-8", "utf-16", "ascii", "latin-1"]
        if self.encoding not in valid_encodings:
            errors.append(f"Invalid encoding: {self.encoding}")

        # Validate line ending
        valid_endings = ["lf", "crlf", "cr"]
        if self.line_ending not in valid_endings:
            errors.append(f"Invalid line ending: {self.line_ending}")

        # Validate indent size
        if not isinstance(self.indent_size, int) or self.indent_size <= 0:
            errors.append("Indent size must be a positive integer")

        # Validate wrap width
        if not isinstance(self.wrap_width, int) or self.wrap_width <= 0:
            errors.append("Wrap width must be a positive integer")

        # Validate extensions
        for ext in self.extensions:
            if ext not in self.supported_extensions:
                warnings.append(f"Unsupported extension: {ext}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Markdown platform.

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

            # Check output directory
            output_dir = Path(self.output_directory)
            if not output_dir.exists() or not output_dir.is_dir():
                return {
                    "healthy": False,
                    "message": "Output directory not accessible",
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Check write permissions
            test_file = output_dir / ".health_check"
            try:
                test_file.write_text("test", encoding=self.encoding)
                test_file.unlink()
            except Exception as e:
                return {
                    "healthy": False,
                    "message": f"Write permission denied: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }

            return {
                "healthy": True,
                "message": "Markdown adapter is operational",
                "timestamp": datetime.utcnow().isoformat(),
                "output_directory": str(output_dir),
                "extensions": self.extensions
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "message": f"Health check error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def validate_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate skill for Markdown platform.

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
            else:
                # Check for invalid filename characters
                invalid_chars = r'[<>:"/\\|?*]'
                if re.search(invalid_chars, skill_data["name"]):
                    errors.append("Skill name contains invalid filename characters")

            # Validate description
            if "description" not in skill_data:
                warnings.append("Skill description is recommended")

            # Validate format
            format_type = skill_data.get("format", "markdown")
            await self._validate_format_specific(skill_data, format_type, errors, warnings)

            # Validate Markdown syntax
            if format_type in ["markdown", "md"]:
                await self._validate_markdown_syntax(skill_data, errors, warnings)

            # Check file size
            content = self._serialize_skill_data(skill_data)
            data_size = len(content.encode(self.encoding))

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
        """Validate skill format for Markdown.

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
            if format_type in ["markdown", "md"]:
                await self._validate_markdown_format(skill_data, errors, warnings)
            elif format_type in ["json", "yaml"]:
                await self._validate_standard_format(skill_data, errors, warnings)

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
        """Validate skill size for Markdown.

        Args:
            skill_data: Skill data

        Returns:
            Size validation result
        """
        content = self._serialize_skill_data(skill_data)
        data_size = len(content.encode(self.encoding))

        format_type = skill_data.get("format", "markdown")
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
        """Convert skill to Markdown format.

        Args:
            skill_data: Source skill data
            source_format: Source format
            target_format: Target format (markdown or md)

        Returns:
            Converted skill data
        """
        try:
            if target_format not in ["markdown", "md"]:
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
        """Convert from Markdown format to standard format.

        Args:
            platform_data: Markdown format data

        Returns:
            Standard format data
        """
        try:
            # Parse frontmatter if present
            if "---\n" in platform_data.get("content", ""):
                return await self._parse_frontmatter(platform_data)
            else:
                return await self._convert_from_plain_markdown(platform_data)

        except Exception as e:
            logger.error(f"Platform conversion error: {str(e)}")
            raise ValidationError(
                f"Failed to convert from Markdown format: {str(e)}",
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
            ("json", "markdown"): {
                "template_type": "json_to_markdown",
                "fields": {
                    "title": "name",
                    "description": "description",
                    "content": "content"
                }
            },
            ("yaml", "markdown"): {
                "template_type": "yaml_to_markdown",
                "fields": {
                    "title": "name",
                    "description": "description",
                    "content": "content"
                }
            },
            ("markdown", "json"): {
                "template_type": "markdown_to_json",
                "parse_frontmatter": True
            },
            ("markdown", "yaml"): {
                "template_type": "markdown_to_yaml",
                "parse_frontmatter": True
            }
        }

        return templates.get((source_format, target_format))

    async def deploy_skill(
        self,
        skill_data: Dict[str, Any],
        deployment_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Deploy skill to Markdown platform.

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

            # Convert to Markdown if needed
            format_type = skill_data.get("format", "markdown")
            if format_type not in ["markdown", "md"]:
                skill_data = await self.convert_skill(
                    skill_data,
                    format_type,
                    "markdown"
                )

            # Generate Markdown document
            result = await self._generate_markdown_document(
                skill_data,
                deployment_id,
                deployment_config
            )

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
        """Get deployment status from Markdown platform.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status
        """
        try:
            # Check if file was created
            output_file = Path(self.output_directory) / f"{deployment_id}.md"

            if not output_file.exists():
                return {
                    "deployment_id": deployment_id,
                    "status": "pending",
                    "platform": self.platform_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

            return {
                "deployment_id": deployment_id,
                "status": "success",
                "platform": self.platform_id,
                "timestamp": datetime.utcnow().isoformat(),
                "file_path": str(output_file),
                "file_size": output_file.stat().st_size
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
            # Remove output file
            output_file = Path(self.output_directory) / f"{deployment_id}.md"
            if output_file.exists():
                output_file.unlink()

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
                raise ValidationError(
                    "Skill data not available for retry",
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
        """Get Markdown platform information.

        Returns:
            Platform information
        """
        return {
            "platform_id": self.platform_id,
            "display_name": self.display_name,
            "platform_type": self.platform_type,
            "output_directory": self.output_directory,
            "encoding": self.encoding,
            "line_ending": self.line_ending,
            "supported_formats": self.supported_formats,
            "supported_extensions": self.supported_extensions,
            "features": self.features,
            "capabilities": [c.value for c in self.capabilities.keys()],
            "max_file_size": self.max_file_size,
            "format_size_limits": self.format_size_limits,
            "adapter_version": self.adapter_version,
            "platform_version": self.platform_version,
            "is_initialized": self.is_initialized
        }

    async def get_supported_models(self) -> List[str]:
        """Get list of supported models.

        Returns:
            Empty list (not applicable for Markdown)
        """
        return []

    async def get_api_limits(self) -> Dict[str, Any]:
        """Get API limits.

        Returns:
            Empty dict (not applicable for Markdown)
        """
        return {}

    async def cleanup(self) -> None:
        """Cleanup adapter resources."""
        try:
            self.is_initialized = False
            logger.info("Markdown adapter cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

    # Private methods

    def _init_output_directory(self) -> None:
        """Initialize output directory."""
        if not self.output_directory:
            self.output_directory = "./output"

    async def _test_jinja2(self) -> None:
        """Test Jinja2 template engine.

        Raises:
            ConfigurationError: If Jinja2 is not available
        """
        try:
            import jinja2
            # Simple template test
            template = jinja2.Template("{{ name }}")
            result = template.render(name="test")
            if result != "test":
                raise ConfigurationError(
                    "Jinja2 template test failed",
                    platform=self.platform_id
                )
        except ImportError:
            raise ConfigurationError(
                "Jinja2 is required for template engine",
                platform=self.platform_id
            )

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

    async def _validate_markdown_syntax(
        self,
        skill_data: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate Markdown syntax.

        Args:
            skill_data: Skill data
            errors: Error list
            warnings: Warning list
        """
        content = skill_data.get("content", "")

        # Check for balanced brackets
        if content.count("[") != content.count("]"):
            errors.append("Unbalanced square brackets in Markdown")

        if content.count("(") != content.count(")"):
            errors.append("Unbalanced parentheses in Markdown")

        # Check for basic heading structure
        lines = content.split("\n")
        for line in lines:
            if line.startswith("#"):
                # Count leading # characters
                level = 0
                for char in line:
                    if char == "#":
                        level += 1
                    else:
                        break

                if level > 6:
                    warnings.append(f"Markdown heading level {level} exceeds 6 (maximum)")

    async def _validate_markdown_format(
        self,
        skill_data: Dict[str, Any],
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Validate Markdown format.

        Args:
            skill_data: Skill data
            errors: Error list
            warnings: Warning list
        """
        # Similar to syntax validation
        await self._validate_markdown_syntax(skill_data, errors, warnings)

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

    def _serialize_skill_data(self, skill_data: Dict[str, Any]) -> str:
        """Serialize skill data to string.

        Args:
            skill_data: Skill data

        Returns:
            Serialized string
        """
        if "content" in skill_data:
            return skill_data["content"]
        elif "markdown" in skill_data:
            return skill_data["markdown"]
        else:
            return json.dumps(skill_data, ensure_ascii=False, indent=2)

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
        template_type = template.get("template_type")

        if template_type == "json_to_markdown":
            return await self._convert_json_to_markdown(skill_data, template)
        elif template_type == "yaml_to_markdown":
            return await self._convert_yaml_to_markdown(skill_data, template)
        elif template_type == "markdown_to_json":
            return await self._convert_markdown_to_json(skill_data, template)
        elif template_type == "markdown_to_yaml":
            return await self._convert_markdown_to_yaml(skill_data, template)
        else:
            raise ValidationError(
                f"Unknown template type: {template_type}",
                platform=self.platform_id
            )

    async def _convert_json_to_markdown(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert JSON to Markdown.

        Args:
            skill_data: Source skill data
            template: Conversion template

        Returns:
            Converted data
        """
        fields = template.get("fields", {})
        markdown_lines = []

        # Title
        title = skill_data.get(fields.get("title", "name"), "Untitled")
        markdown_lines.append(f"# {title}\n")

        # Description
        if fields.get("description") in skill_data:
            description = skill_data[fields["description"]]
            markdown_lines.append(f"{description}\n")

        # Content
        if fields.get("content") in skill_data:
            content = skill_data[fields["content"]]
            markdown_lines.append(f"{content}\n")

        return {
            "format": "markdown",
            "content": "\n".join(markdown_lines),
            "metadata": {
                "title": title,
                "source": "json",
                "converted_at": datetime.utcnow().isoformat()
            }
        }

    async def _convert_yaml_to_markdown(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert YAML to Markdown.

        Args:
            skill_data: Source skill data
            template: Conversion template

        Returns:
            Converted data
        """
        # Similar to JSON conversion
        return await self._convert_json_to_markdown(skill_data, template)

    async def _convert_markdown_to_json(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Markdown to JSON.

        Args:
            skill_data: Source skill data
            template: Conversion template

        Returns:
            Converted data
        """
        content = skill_data.get("content", "")

        # Parse frontmatter if enabled
        if template.get("parse_frontmatter"):
            frontmatter, body = await self._parse_frontmatter({"content": content})
            if frontmatter:
                return {
                    "format": "json",
                    "data": frontmatter,
                    "content": body,
                    "metadata": {
                        "source": "markdown",
                        "converted_at": datetime.utcnow().isoformat()
                    }
                }

        return {
            "format": "json",
            "content": content,
            "metadata": {
                "source": "markdown",
                "converted_at": datetime.utcnow().isoformat()
            }
        }

    async def _convert_markdown_to_yaml(
        self,
        skill_data: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Markdown to YAML.

        Args:
            skill_data: Source skill data
            template: Conversion template

        Returns:
            Converted data
        """
        # Similar to JSON conversion
        return await self._convert_markdown_to_json(skill_data, template)

    async def _parse_frontmatter(self, platform_data: Dict[str, Any]) -> tuple:
        """Parse YAML frontmatter from Markdown.

        Args:
            platform_data: Platform data

        Returns:
            Tuple of (frontmatter_dict, body_string)
        """
        content = platform_data.get("content", "")

        if not content.startswith("---\n"):
            return None, content

        try:
            # Find closing frontmatter
            end_marker = content.find("\n---\n")
            if end_marker == -1:
                return None, content

            # Extract frontmatter
            frontmatter_yaml = content[4:end_marker]
            body = content[end_marker + 5:]

            # Parse YAML
            import yaml
            frontmatter = yaml.safe_load(frontmatter_yaml)

            return frontmatter, body

        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {str(e)}")
            return None, content

    async def _convert_from_plain_markdown(self, platform_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert from plain Markdown.

        Args:
            platform_data: Platform data

        Returns:
            Standard format data
        """
        content = platform_data.get("content", "")

        # Extract title from first heading
        title = "Untitled"
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        return {
            "name": title,
            "format": "markdown",
            "content": content,
            "metadata": {
                "source": "markdown",
                "converted_at": datetime.utcnow().isoformat()
            }
        }

    async def _generate_markdown_document(
        self,
        skill_data: Dict[str, Any],
        deployment_id: str,
        deployment_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Markdown document.

        Args:
            skill_data: Skill data
            deployment_id: Deployment ID
            deployment_config: Deployment config

        Returns:
            Deployment result
        """
        # Prepare content
        content = skill_data.get("content", "")

        # Add frontmatter if configured
        if deployment_config and deployment_config.get("add_frontmatter", False):
            frontmatter = {
                "title": skill_data.get("name", "Untitled"),
                "description": skill_data.get("description", ""),
                "created_at": datetime.utcnow().isoformat(),
                "deployment_id": deployment_id
            }

            import yaml
            frontmatter_yaml = yaml.safe_dump(frontmatter, default_flow_style=False)
            content = f"---\n{frontmatter_yaml}---\n\n{content}"

        # Write to file
        output_file = Path(self.output_directory) / f"{deployment_id}.md"
        output_file.write_text(content, encoding=self.encoding)

        # Apply line ending conversion
        if self.line_ending == "crlf":
            content = content.replace("\n", "\r\n")
        elif self.line_ending == "cr":
            content = content.replace("\n", "\r")

        return {
            "deployment_id": deployment_id,
            "status": "success",
            "platform": self.platform_id,
            "file_path": str(output_file),
            "file_size": output_file.stat().st_size,
            "timestamp": datetime.utcnow().isoformat(),
            "format": "markdown"
        }

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle Markdown-specific errors.

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

        # Add Markdown-specific error details
        if isinstance(error, FileNotFoundError):
            error_info["category"] = "file_not_found"
        elif isinstance(error, PermissionError):
            error_info["category"] = "permission_error"

        return error_info

    def is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error is retryable
        """
        # Markdown retryable errors
        retryable_errors = (
            "PermissionError",
            "FileNotFoundError",
            "OSError"
        )

        return isinstance(error, tuple(type(e) for e in retryable_errors))