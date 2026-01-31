"""Skill validators.

This module provides validation utilities for skill data,
content validation, and business rule enforcement.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import yaml
import json

logger = logging.getLogger(__name__)


class SkillValidator:
    """Validator for skill data and content."""

    # Validation patterns
    NAME_PATTERN = r"^[a-zA-Z0-9\s\-_]+$"
    VERSION_PATTERN = r"^\d+(\.\d+){0,3}(-[a-zA-Z0-9\-]+)?$"
    KEYWORD_PATTERN = r"^[a-z0-9\-]+$"
    TAG_PATTERN = r"^[a-zA-Z0-9\s\-_]+$"
    DEPENDENCY_PATTERN = r"^[a-zA-Z0-9\-_.]+"
    PYTHON_VERSION_PATTERN = r"^(>=|<=|>|<|==|!=)?\s*\d+(\.\d+){0,2}$"

    # Validation limits
    MAX_NAME_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 5000
    MAX_KEYWORDS = 20
    MAX_KEYWORD_LENGTH = 50
    MAX_DEPENDENCIES = 100
    MAX_DEPENDENCY_LENGTH = 200
    MAX_TAGS = 20
    MAX_TAG_LENGTH = 50
    MAX_CONTENT_SIZE = 1000000  # 1MB
    MAX_CONFIG_SIZE = 10000  # 10KB

    @classmethod
    def validate_skill_name(cls, name: str) -> Tuple[bool, Optional[str]]:
        """Validate skill name.

        Args:
            name: Skill name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Skill name cannot be empty"

        name = name.strip()

        if len(name) > cls.MAX_NAME_LENGTH:
            return False, f"Skill name cannot exceed {cls.MAX_NAME_LENGTH} characters"

        if not re.match(cls.NAME_PATTERN, name):
            return False, "Skill name contains invalid characters. Use letters, numbers, spaces, hyphens, and underscores only"

        return True, None

    @classmethod
    def validate_skill_version(cls, version: str) -> Tuple[bool, Optional[str]]:
        """Validate skill version using semantic versioning.

        Args:
            version: Version string to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not version:
            return False, "Version cannot be empty"

        if not re.match(cls.VERSION_PATTERN, version):
            return False, "Invalid version format. Use semantic versioning (e.g., '1.0.0', '2.1.3', '1.0.0-alpha')"

        return True, None

    @classmethod
    def validate_keywords(cls, keywords: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate keywords list.

        Args:
            keywords: List of keywords to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not keywords:
            return True, None

        if len(keywords) > cls.MAX_KEYWORDS:
            return False, f"Maximum {cls.MAX_KEYWORDS} keywords allowed"

        for keyword in keywords:
            keyword = keyword.strip().lower()

            if not keyword:
                return False, "Keywords cannot be empty"

            if len(keyword) > cls.MAX_KEYWORD_LENGTH:
                return False, f"Keyword '{keyword}' exceeds {cls.MAX_KEYWORD_LENGTH} characters"

            if not re.match(cls.KEYWORD_PATTERN, keyword):
                return False, f"Keyword '{keyword}' contains invalid characters. Use lowercase letters, numbers, and hyphens only"

        return True, None

    @classmethod
    def validate_tags(cls, tags: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate tags list.

        Args:
            tags: List of tags to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not tags:
            return True, None

        if len(tags) > cls.MAX_TAGS:
            return False, f"Maximum {cls.MAX_TAGS} tags allowed"

        for tag in tags:
            tag = tag.strip()

            if not tag:
                return False, "Tags cannot be empty"

            if len(tag) > cls.MAX_TAG_LENGTH:
                return False, f"Tag '{tag}' exceeds {cls.MAX_TAG_LENGTH} characters"

            if not re.match(cls.TAG_PATTERN, tag):
                return False, f"Tag '{tag}' contains invalid characters"

        return True, None

    @classmethod
    def validate_dependencies(cls, dependencies: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate dependencies list.

        Args:
            dependencies: List of dependencies to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not dependencies:
            return True, None

        if len(dependencies) > cls.MAX_DEPENDENCIES:
            return False, f"Maximum {cls.MAX_DEPENDENCIES} dependencies allowed"

        for dependency in dependencies:
            dependency = dependency.strip()

            if not dependency:
                return False, "Dependencies cannot be empty"

            if len(dependency) > cls.MAX_DEPENDENCY_LENGTH:
                return False, f"Dependency '{dependency}' exceeds {cls.MAX_DEPENDENCY_LENGTH} characters"

            if not re.match(cls.DEPENDENCY_PATTERN, dependency):
                return False, f"Dependency '{dependency}' has invalid format"

        return True, None

    @classmethod
    def validate_content(cls, content: str) -> Tuple[bool, Optional[str]]:
        """Validate skill content.

        Args:
            content: Content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content or not content.strip():
            return False, "Content cannot be empty"

        content = content.strip()

        if len(content) > cls.MAX_CONTENT_SIZE:
            return False, f"Content too large (maximum {cls.MAX_CONTENT_SIZE // 1024 // 1024}MB)"

        # Check minimum content requirements
        lines = content.splitlines()
        if len(lines) < 3:
            return False, "Content must have at least 3 lines"

        return True, None

    @classmethod
    def validate_python_requires(cls, python_requires: str) -> Tuple[bool, Optional[str]]:
        """Validate Python version requirement.

        Args:
            python_requires: Python version requirement string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not python_requires:
            return True, None

        if not re.match(cls.PYTHON_VERSION_PATTERN, python_requires):
            return False, "Invalid Python version format. Use formats like '>=3.8', '==3.9', '<4.0'"

        return True, None

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate skill configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not config:
            return True, None

        config_str = str(config)
        if len(config_str) > cls.MAX_CONFIG_SIZE:
            return False, f"Configuration too large (maximum {cls.MAX_CONFIG_SIZE // 1024}KB)"

        # Check nested depth
        def check_depth(obj, depth=0, max_depth=5):
            if depth > max_depth:
                return False, f"Configuration nested too deeply (maximum {max_depth} levels)"

            if isinstance(obj, dict):
                for value in obj.values():
                    if not check_depth(value, depth + 1, max_depth):
                        return False
            elif isinstance(obj, list):
                for item in obj:
                    if not check_depth(item, depth + 1, max_depth):
                        return False

            return True

        if not check_depth(config):
            return False, "Configuration nested too deeply (maximum 5 levels)"

        return True, None

    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, Optional[str]]:
        """Validate URL format.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return True, None

        try:
            result = urlparse(url)
            if not result.scheme or not result.netloc:
                return False, "Invalid URL format"

            if result.scheme not in ['http', 'https']:
                return False, "URL must use HTTP or HTTPS protocol"

        except Exception:
            return False, "Invalid URL format"

        return True, None

    @classmethod
    def validate_skill_data(cls, skill_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate complete skill data.

        Args:
            skill_data: Skill data dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate required fields
        if "name" in skill_data:
            is_valid, error = cls.validate_skill_name(skill_data["name"])
            if not is_valid:
                errors.append(f"Name: {error}")

        if "version" in skill_data:
            is_valid, error = cls.validate_skill_version(skill_data["version"])
            if not is_valid:
                errors.append(f"Version: {error}")

        # Validate optional fields
        if "keywords" in skill_data:
            is_valid, error = cls.validate_keywords(skill_data["keywords"])
            if not is_valid:
                errors.append(f"Keywords: {error}")

        if "tags" in skill_data:
            is_valid, error = cls.validate_tags(skill_data["tags"])
            if not is_valid:
                errors.append(f"Tags: {error}")

        if "dependencies" in skill_data:
            is_valid, error = cls.validate_dependencies(skill_data["dependencies"])
            if not is_valid:
                errors.append(f"Dependencies: {error}")

        if "python_requires" in skill_data:
            is_valid, error = cls.validate_python_requires(skill_data["python_requires"])
            if not is_valid:
                errors.append(f"Python requires: {error}")

        if "config" in skill_data:
            is_valid, error = cls.validate_config(skill_data["config"])
            if not is_valid:
                errors.append(f"Config: {error}")

        # Validate URLs
        url_fields = ["homepage", "repository", "documentation"]
        for field in url_fields:
            if field in skill_data and skill_data[field]:
                is_valid, error = cls.validate_url(skill_data[field])
                if not is_valid:
                    errors.append(f"{field.title()}: {error}")

        return len(errors) == 0, errors


class ContentValidator:
    """Validator for skill content formats."""

    @classmethod
    def validate_yaml_content(cls, content: str) -> Tuple[bool, Optional[str]]:
        """Validate YAML content.

        Args:
            content: YAML content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content:
            return False, "Content cannot be empty"

        try:
            yaml.safe_load(content)
            return True, None
        except yaml.YAMLError as e:
            return False, f"Invalid YAML format: {str(e)}"

    @classmethod
    def validate_json_content(cls, content: str) -> Tuple[bool, Optional[str]]:
        """Validate JSON content.

        Args:
            content: JSON content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not content:
            return False, "Content cannot be empty"

        try:
            json.loads(content)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"

    @classmethod
    def validate_content_format(cls, content: str, format_type: str) -> Tuple[bool, Optional[str]]:
        """Validate content based on format.

        Args:
            content: Content to validate
            format_type: Content format (yaml, json, etc.)

        Returns:
            Tuple of (is_valid, error_message)
        """
        format_validators = {
            "yaml": cls.validate_yaml_content,
            "json": cls.validate_json_content,
        }

        if format_type.lower() not in format_validators:
            return False, f"Unsupported content format: {format_type}"

        validator = format_validators[format_type.lower()]
        return validator(content)

    @classmethod
    def extract_content_metadata(cls, content: str, format_type: str) -> Dict[str, Any]:
        """Extract metadata from content.

        Args:
            content: Content to analyze
            format_type: Content format

        Returns:
            Dictionary containing metadata
        """
        metadata = {
            "line_count": len(content.splitlines()),
            "character_count": len(content),
            "word_count": len(content.split()),
            "size_bytes": len(content.encode("utf-8")),
        }

        try:
            if format_type.lower() == "yaml":
                parsed = yaml.safe_load(content)
                if isinstance(parsed, dict):
                    metadata["has_root_dict"] = True
                    metadata["root_keys"] = list(parsed.keys())
                    metadata["has_name"] = "name" in parsed
                    metadata["has_version"] = "version" in parsed
                    metadata["has_description"] = "description" in parsed

            elif format_type.lower() == "json":
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    metadata["has_root_dict"] = True
                    metadata["root_keys"] = list(parsed.keys())
                    metadata["has_name"] = "name" in parsed
                    metadata["has_version"] = "version" in parsed
                    metadata["has_description"] = "description" in parsed

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")

        return metadata


class BusinessRuleValidator:
    """Validator for business rules and constraints."""

    @classmethod
    def validate_skill_uniqueness(cls, name: str, slug: str, existing_skills: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        """Validate skill uniqueness against existing skills.

        Args:
            name: Skill name
            slug: Skill slug
            existing_skills: List of existing skills

        Returns:
            Tuple of (is_valid, error_message)
        """
        for skill in existing_skills:
            if skill.get("name", "").lower() == name.lower():
                return False, f"Skill with name '{name}' already exists"

            if skill.get("slug", "").lower() == slug.lower():
                return False, f"Skill with slug '{slug}' already exists"

        return True, None

    @classmethod
    def validate_category_access(cls, category_id: str, user_permissions: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate if user has access to category.

        Args:
            category_id: Category ID
            user_permissions: User permissions

        Returns:
            Tuple of (is_valid, error_message)
        """
        # This would check actual user permissions
        # For now, we'll just check if the category exists
        # In a real implementation, this would query the database

        if not category_id:
            return True, None

        # Basic validation - check if it's a valid UUID format
        if not re.match(r"^[a-f0-9\-]{36}$", category_id):
            return False, "Invalid category ID format"

        return True, None

    @classmethod
    def validate_version_compatibility(cls, version: str, python_requires: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate version compatibility with Python requirements.

        Args:
            version: Skill version
            python_requires: Python version requirement

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not python_requires:
            return True, None

        # This would implement actual version compatibility checking
        # For now, we'll just do basic format validation

        if not re.match(r"^\d+\.\d+", version):
            return False, "Version must start with major.minor format"

        # Additional compatibility logic would go here
        return True, None

    @classmethod
    def validate_dependency_compatibility(cls, dependencies: List[str]) -> Tuple[bool, List[str]]:
        """Validate dependency compatibility and conflicts.

        Args:
            dependencies: List of dependencies

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []

        # Check for duplicate dependencies
        seen_deps = set()
        for dep in dependencies:
            if dep in seen_deps:
                warnings.append(f"Duplicate dependency detected: {dep}")
            seen_deps.add(dep)

        # Check for common conflicts
        conflict_pairs = [
            ("tensorflow", "keras"),  # These have specific compatibility requirements
            ("python-dateutil", "dateutil"),
        ]

        deps_lower = [dep.lower() for dep in dependencies]
        for dep1, dep2 in conflict_pairs:
            if dep1 in deps_lower and dep2 in deps_lower:
                warnings.append(f"Potential conflict between {dep1} and {dep2}")

        return len(warnings) == 0, warnings
