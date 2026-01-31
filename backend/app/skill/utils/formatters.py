"""Skill formatters.

This module provides formatting utilities for skill data,
output formatting, and display formatting.
"""

import re
import json
import yaml
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import quote


class SkillFormatter:
    """Formatter for skill data and metadata."""

    @staticmethod
    def format_skill_name(name: str) -> str:
        """Format skill name for display.

        Args:
            name: Raw skill name

        Returns:
            Formatted skill name
        """
        if not name:
            return ""

        # Clean and format
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)  # Normalize whitespace

        return name

    @staticmethod
    def format_skill_slug(name: str) -> str:
        """Generate URL-friendly slug from skill name.

        Args:
            name: Skill name

        Returns:
            URL-friendly slug
        """
        if not name:
            return ""

        # Convert to lowercase
        slug = name.lower().strip()

        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)

        # Remove special characters except hyphens
        slug = re.sub(r'[^a-z0-9\-]', '', slug)

        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Ensure slug is not empty
        if not slug:
            slug = "skill"

        return slug

    @staticmethod
    def format_version(version: str) -> str:
        """Format version string.

        Args:
            version: Raw version string

        Returns:
            Formatted version
        """
        if not version:
            return "1.0.0"

        # Clean version string
        version = version.strip()

        # Ensure it starts with a digit
        if not re.match(r'^\d', version):
            version = "1.0.0"

        return version

    @staticmethod
    def format_keywords(keywords: List[str]) -> List[str]:
        """Format keywords list.

        Args:
            keywords: List of keywords

        Returns:
            Formatted keywords
        """
        if not keywords:
            return []

        # Clean and normalize
        formatted = []
        seen = set()

        for keyword in keywords:
            keyword = keyword.strip().lower()
            if keyword and keyword not in seen:
                formatted.append(keyword)
                seen.add(keyword)

        return formatted

    @staticmethod
    def format_tags(tags: List[str]) -> List[str]:
        """Format tags list.

        Args:
            tags: List of tags

        Returns:
            Formatted tags
        """
        if not tags:
            return []

        # Clean and normalize
        formatted = []
        seen = set()

        for tag in tags:
            tag = tag.strip()
            if tag and tag not in seen:
                formatted.append(tag)
                seen.add(tag)

        return formatted

    @staticmethod
    def format_description(description: str) -> str:
        """Format skill description.

        Args:
            description: Raw description

        Returns:
            Formatted description
        """
        if not description:
            return ""

        # Clean description
        description = description.strip()

        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description)

        # Limit length if too long (for preview)
        if len(description) > 500:
            description = description[:500] + "..."

        return description

    @staticmethod
    def format_dependencies(dependencies: List[str]) -> List[str]:
        """Format dependencies list.

        Args:
            dependencies: List of dependencies

        Returns:
            Formatted dependencies
        """
        if not dependencies:
            return []

        # Clean and normalize
        formatted = []
        seen = set()

        for dep in dependencies:
            dep = dep.strip()
            if dep and dep not in seen:
                formatted.append(dep)
                seen.add(dep)

        return formatted

    @staticmethod
    def format_rating(rating: float, rating_count: int) -> str:
        """Format rating for display.

        Args:
            rating: Rating value
            rating_count: Number of ratings

        Returns:
            Formatted rating string
        """
        if rating_count == 0:
            return "No ratings"

        # Format to 1 decimal place
        formatted_rating = f"{rating:.1f}"

        return f"{formatted_rating}/5 ({rating_count} ratings)"

    @staticmethod
    def format_download_count(count: int) -> str:
        """Format download count for display.

        Args:
            count: Download count

        Returns:
            Formatted count string
        """
        if count == 0:
            return "No downloads"

        if count < 1000:
            return str(count)

        if count < 1000000:
            return f"{count/1000:.1f}k"

        return f"{count/1000000:.1f}M"

    @staticmethod
    def format_datetime(dt: Optional[datetime]) -> str:
        """Format datetime for display.

        Args:
            dt: Datetime object

        Returns:
            Formatted datetime string
        """
        if not dt:
            return "Unknown"

        # Format as ISO string
        return dt.isoformat()

    @staticmethod
    def format_python_requires(python_requires: str) -> str:
        """Format Python version requirement.

        Args:
            python_requires: Python version requirement

        Returns:
            Formatted requirement
        """
        if not python_requires:
            return "Any Python version"

        # Clean up formatting
        python_requires = python_requires.strip()

        # Ensure proper spacing around operators
        python_requires = re.sub(r'(\d)(>=|<=|>|<|==|!=)', r'\1 \2', python_requires)
        python_requires = re.sub(r'(>=|<=|>|<|==|!=)(\d)', r'\1 \2', python_requires)

        return python_requires


class SkillDisplayFormatter:
    """Formatter for displaying skill information."""

    @staticmethod
    def format_skill_card(skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format skill data for card display.

        Args:
            skill_data: Raw skill data

        Returns:
            Formatted skill data for display
        """
        # Format basic fields
        formatted = {
            "id": skill_data.get("id", ""),
            "name": SkillFormatter.format_skill_name(skill_data.get("name", "")),
            "slug": skill_data.get("slug", ""),
            "description": SkillFormatter.format_description(skill_data.get("description", "")),
            "version": SkillFormatter.format_version(skill_data.get("version", "")),
            "status": skill_data.get("status", "draft"),
            "visibility": skill_data.get("visibility", "private"),
            "author": skill_data.get("author", "Unknown"),
        }

        # Format statistics
        rating = skill_data.get("rating", 0)
        rating_count = skill_data.get("rating_count", 0)
        formatted["rating"] = SkillFormatter.format_rating(rating, rating_count)

        download_count = skill_data.get("download_count", 0)
        formatted["download_count"] = SkillFormatter.format_download_count(download_count)

        # Format dates
        created_at = skill_data.get("created_at")
        formatted["created_at"] = SkillFormatter.format_datetime(created_at)

        # Format tags
        tags = skill_data.get("tags", [])
        formatted["tags"] = SkillFormatter.format_tags(tags)

        # Format keywords
        keywords = skill_data.get("keywords", [])
        formatted["keywords"] = SkillFormatter.format_keywords(keywords)

        # Format category
        category = skill_data.get("category")
        if category:
            formatted["category"] = {
                "id": category.get("id", ""),
                "name": category.get("name", "Unknown"),
            }
        else:
            formatted["category"] = None

        # Add display flags
        formatted["is_active"] = skill_data.get("status") == "active"
        formatted["is_public"] = skill_data.get("visibility") == "public"
        formatted["is_featured"] = skill_data.get("quality_score", 0) >= 80

        return formatted

    @staticmethod
    def format_skill_detail(skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format skill data for detailed display.

        Args:
            skill_data: Raw skill data

        Returns:
            Formatted skill data for detail view
        """
        # Start with card format
        formatted = SkillDisplayFormatter.format_skill_card(skill_data)

        # Add detail-specific fields
        formatted["full_description"] = skill_data.get("description", "")
        formatted["license"] = skill_data.get("license", "Unknown")
        formatted["maintainer"] = skill_data.get("maintainer", "Unknown")

        # Format URLs
        formatted["homepage"] = skill_data.get("homepage")
        formatted["repository"] = skill_data.get("repository")
        formatted["documentation"] = skill_data.get("documentation")

        # Format Python requirements
        python_requires = skill_data.get("python_requires")
        formatted["python_requires"] = SkillFormatter.format_python_requires(python_requires)

        # Format dependencies
        dependencies = skill_data.get("dependencies", [])
        formatted["dependencies"] = SkillFormatter.format_dependencies(dependencies)

        # Format config
        config = skill_data.get("config")
        if config:
            formatted["config"] = json.dumps(config, indent=2)
        else:
            formatted["config"] = None

        # Add more statistics
        formatted["view_count"] = skill_data.get("view_count", 0)
        formatted["like_count"] = skill_data.get("like_count", 0)
        formatted["quality_score"] = skill_data.get("quality_score", 0)
        formatted["completeness"] = skill_data.get("completeness", 0)

        # Format all timestamps
        timestamps = [
            "created_at", "updated_at", "published_at",
            "deprecated_at", "archived_at"
        ]

        for timestamp in timestamps:
            if timestamp in skill_data:
                formatted[timestamp] = SkillFormatter.format_datetime(skill_data[timestamp])

        return formatted


class JSONFormatter:
    """Formatter for JSON output."""

    @staticmethod
    def format_skill_json(skill_data: Dict[str, Any], pretty: bool = True) -> str:
        """Format skill data as JSON.

        Args:
            skill_data: Skill data
            pretty: Whether to pretty-print

        Returns:
            JSON string
        """
        indent = 2 if pretty else None

        try:
            return json.dumps(skill_data, indent=indent, ensure_ascii=False, default=str)
        except Exception as e:
            return f'{{"error": "Failed to format JSON: {str(e)}"}}'

    @staticmethod
    def parse_json(json_str: str) -> Tuple[bool, Any]:
        """Parse JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            Tuple of (is_valid, parsed_data)
        """
        try:
            data = json.loads(json_str)
            return True, data
        except json.JSONDecodeError as e:
            return False, str(e)


class YAMLFormatter:
    """Formatter for YAML output."""

    @staticmethod
    def format_skill_yaml(skill_data: Dict[str, Any], safe: bool = True) -> str:
        """Format skill data as YAML.

        Args:
            skill_data: Skill data
            safe: Whether to use safe_dump

        Returns:
            YAML string
        """
        try:
            if safe:
                return yaml.safe_dump(skill_data, default_flow_style=False, allow_unicode=True)
            else:
                return yaml.dump(skill_data, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            return f"# Error formatting YAML: {str(e)}"

    @staticmethod
    def parse_yaml(yaml_str: str) -> Tuple[bool, Any]:
        """Parse YAML string.

        Args:
            yaml_str: YAML string to parse

        Returns:
            Tuple of (is_valid, parsed_data)
        """
        try:
            data = yaml.safe_load(yaml_str)
            return True, data
        except yaml.YAMLError as e:
            return False, str(e)


class MarkdownFormatter:
    """Formatter for Markdown output."""

    @staticmethod
    def format_skill_markdown(skill_data: Dict[str, Any]) -> str:
        """Format skill data as Markdown.

        Args:
            skill_data: Skill data

        Returns:
            Markdown string
        """
        lines = []

        # Title
        name = skill_data.get("name", "Untitled Skill")
        version = skill_data.get("version", "1.0.0")
        lines.append(f"# {name} v{version}")
        lines.append("")

        # Description
        description = skill_data.get("description")
        if description:
            lines.append("## Description")
            lines.append(description)
            lines.append("")

        # Metadata
        lines.append("## Metadata")
        metadata_items = [
            ("Author", skill_data.get("author")),
            ("Maintainer", skill_data.get("maintainer")),
            ("License", skill_data.get("license")),
            ("Version", skill_data.get("version")),
            ("Status", skill_data.get("status")),
            ("Visibility", skill_data.get("visibility")),
            ("Created", SkillFormatter.format_datetime(skill_data.get("created_at"))),
            ("Updated", SkillFormatter.format_datetime(skill_data.get("updated_at"))),
        ]

        for key, value in metadata_items:
            if value:
                lines.append(f"- **{key}**: {value}")

        lines.append("")

        # Category and Tags
        category = skill_data.get("category")
        if category:
            lines.append("## Category")
            lines.append(f"- **Name**: {category.get('name', 'Unknown')}")
            lines.append("")

        tags = skill_data.get("tags", [])
        if tags:
            lines.append("## Tags")
            for tag in tags:
                lines.append(f"- {tag}")
            lines.append("")

        # Keywords
        keywords = skill_data.get("keywords", [])
        if keywords:
            lines.append("## Keywords")
            lines.append(", ".join(keywords))
            lines.append("")

        # Dependencies
        dependencies = skill_data.get("dependencies", [])
        if dependencies:
            lines.append("## Dependencies")
            for dep in dependencies:
                lines.append(f"- {dep}")
            lines.append("")

        # URLs
        urls = [
            ("Homepage", skill_data.get("homepage")),
            ("Repository", skill_data.get("repository")),
            ("Documentation", skill_data.get("documentation")),
        ]

        url_lines = [f"- **{name}**: [{url}]({url})" for name, url in urls if url]
        if url_lines:
            lines.append("## URLs")
            lines.extend(url_lines)
            lines.append("")

        # Statistics
        lines.append("## Statistics")
        stats_items = [
            ("Downloads", SkillFormatter.format_download_count(skill_data.get("download_count", 0))),
            ("Views", skill_data.get("view_count", 0)),
            ("Likes", skill_data.get("like_count", 0)),
            ("Rating", SkillFormatter.format_rating(
                skill_data.get("rating", 0),
                skill_data.get("rating_count", 0)
            )),
            ("Quality Score", skill_data.get("quality_score", 0)),
            ("Completeness", skill_data.get("completeness", 0)),
        ]

        for key, value in stats_items:
            lines.append(f"- **{key}**: {value}")

        return "\n".join(lines)


class CSVFormatter:
    """Formatter for CSV output."""

    @staticmethod
    def format_skills_csv(skills_data: List[Dict[str, Any]]) -> str:
        """Format list of skills as CSV.

        Args:
            skills_data: List of skill data

        Returns:
            CSV string
        """
        if not skills_data:
            return ""

        # Define columns
        columns = [
            "id", "name", "slug", "description", "version", "status",
            "visibility", "author", "maintainer", "license",
            "download_count", "view_count", "like_count",
            "rating", "rating_count", "quality_score", "completeness",
            "created_at", "updated_at"
        ]

        lines = []
        lines.append(",".join(columns))

        # Add data rows
        for skill in skills_data:
            row = []
            for col in columns:
                value = skill.get(col, "")
                # Escape CSV values
                if isinstance(value, str) and ("," in value or '"' in value or "\n" in value):
                    value = '"' + value.replace('"', '""') + '"'
                row.append(str(value))
            lines.append(",".join(row))

        return "\n".join(lines)


class TableFormatter:
    """Formatter for table output."""

    @staticmethod
    def format_skills_table(skills_data: List[Dict[str, Any]], max_width: int = 80) -> str:
        """Format skills as a table.

        Args:
            skills_data: List of skill data
            max_width: Maximum table width

        Returns:
            Formatted table string
        """
        if not skills_data:
            return "No skills found."

        # Define columns
        columns = [
            ("Name", lambda x: x.get("name", "")[:30]),
            ("Version", lambda x: x.get("version", "")),
            ("Status", lambda x: x.get("status", "")[:10]),
            ("Rating", lambda x: f"{x.get('rating', 0):.1f}"),
            ("Downloads", lambda x: SkillFormatter.format_download_count(x.get("download_count", 0))),
        ]

        # Calculate column widths
        col_widths = []
        for col_name, col_func in columns:
            max_len = len(col_name)
            for skill in skills_data:
                value = col_func(skill)
                max_len = max(max_len, len(str(value)))
            col_widths.append(min(max_len + 2, max_width // len(columns)))

        # Build table
        lines = []

        # Header
        header = []
        for i, (col_name, _) in enumerate(columns):
            header.append(col_name.ljust(col_widths[i]))
        lines.append("".join(header))
        lines.append("-" * sum(col_widths))

        # Data rows
        for skill in skills_data:
            row = []
            for i, (_, col_func) in enumerate(columns):
                value = str(col_func(skill))
                # Truncate if too long
                if len(value) > col_widths[i]:
                    value = value[:col_widths[i]-3] + "..."
                row.append(value.ljust(col_widths[i]))
            lines.append("".join(row))

        return "\n".join(lines)
