"""Skill management utilities.

This module exports all skill-related utility functions including
validators, formatters, and templates.
"""

from .validators import (
    SkillValidator,
    ContentValidator,
    BusinessRuleValidator,
)

from .formatters import (
    SkillFormatter,
    SkillDisplayFormatter,
    JSONFormatter,
    YAMLFormatter,
    MarkdownFormatter,
    CSVFormatter,
    TableFormatter,
)

from .templates import (
    SkillTemplate,
    SkillTemplateManager,
    TemplateValidator,
    TemplateRenderer,
)

__all__ = [
    # Validators
    "SkillValidator",
    "ContentValidator",
    "BusinessRuleValidator",
    # Formatters
    "SkillFormatter",
    "SkillDisplayFormatter",
    "JSONFormatter",
    "YAMLFormatter",
    "MarkdownFormatter",
    "CSVFormatter",
    "TableFormatter",
    # Templates
    "SkillTemplate",
    "SkillTemplateManager",
    "TemplateValidator",
    "TemplateRenderer",
]

# Utility groups for easy reference
UTILITY_GROUPS = {
    "validators": [
        "SkillValidator",
        "ContentValidator",
        "BusinessRuleValidator",
    ],
    "formatters": [
        "SkillFormatter",
        "SkillDisplayFormatter",
        "JSONFormatter",
        "YAMLFormatter",
        "MarkdownFormatter",
        "CSVFormatter",
        "TableFormatter",
    ],
    "templates": [
        "SkillTemplate",
        "SkillTemplateManager",
        "TemplateValidator",
        "TemplateRenderer",
    ],
}

# Common configuration
DEFAULT_CONFIG = {
    "validator": {
        "max_content_size": 1000000,  # 1MB
        "max_keywords": 20,
        "max_dependencies": 100,
        "max_tags": 20,
        "max_config_size": 10000,  # 10KB
    },
    "formatter": {
        "json_indent": 2,
        "yaml_safe_dump": True,
        "table_max_width": 80,
        "csv_escape_quotes": True,
    },
    "template": {
        "cache_templates": True,
        "validate_before_render": True,
        "strict_variable_checking": False,
    },
}

# Helper functions
def validate_skill_data(skill_data: dict) -> tuple:
    """Validate skill data using SkillValidator.

    Args:
        skill_data: Skill data dictionary

    Returns:
        Tuple of (is_valid, errors)
    """
    return SkillValidator.validate_skill_data(skill_data)


def format_skill_for_display(skill_data: dict, detail_level: str = "card") -> dict:
    """Format skill data for display.

    Args:
        skill_data: Skill data dictionary
        detail_level: Display level ("card" or "detail")

    Returns:
        Formatted skill data
    """
    if detail_level == "detail":
        return SkillDisplayFormatter.format_skill_detail(skill_data)
    else:
        return SkillDisplayFormatter.format_skill_card(skill_data)


def create_skill_from_template(template_name: str, variables: dict) -> tuple:
    """Create skill data from template.

    Args:
        template_name: Name of template
        variables: Template variables

    Returns:
        Tuple of (is_valid, skill_data, error_message)
    """
    return SkillTemplateManager.render_template(template_name, variables)


def format_output(data: Any, format_type: str, **kwargs) -> str:
    """Format data for output.

    Args:
        data: Data to format
        format_type: Output format ("json", "yaml", "markdown", "csv", "table")
        **kwargs: Additional formatting options

    Returns:
        Formatted string
    """
    if format_type == "json":
        return JSONFormatter.format_skill_json(data, **kwargs)
    elif format_type == "yaml":
        return YAMLFormatter.format_skill_yaml(data, **kwargs)
    elif format_type == "markdown":
        return MarkdownFormatter.format_skill_markdown(data)
    elif format_type == "csv" and isinstance(data, list):
        return CSVFormatter.format_skills_csv(data)
    elif format_type == "table" and isinstance(data, list):
        return TableFormatter.format_skills_table(data, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format_type}")
