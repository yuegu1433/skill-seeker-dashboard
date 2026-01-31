"""Skill templates.

This module provides template utilities for skill creation,
including predefined templates and template rendering.
"""

import re
import yaml
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class SkillTemplate:
    """Base class for skill templates."""

    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        content_format: str = "yaml",
        version: str = "1.0.0",
        keywords: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize skill template.

        Args:
            name: Template name
            description: Template description
            content: Template content
            content_format: Format of content (yaml, json, etc.)
            version: Default version
            keywords: Default keywords
            dependencies: Default dependencies
            config: Default configuration
        """
        self.name = name
        self.description = description
        self.content = content
        self.content_format = content_format
        self.version = version
        self.keywords = keywords or []
        self.dependencies = dependencies or []
        self.config = config or {}

    def render(self, variables: Dict[str, Any]) -> str:
        """Render template with variables.

        Args:
            variables: Dictionary of variables to replace

        Returns:
            Rendered content
        """
        content = self.content

        # Simple variable replacement
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}"
            content = content.replace(placeholder, str(value))

        return content

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary.

        Returns:
            Template as dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "content_format": self.content_format,
            "version": self.version,
            "keywords": self.keywords,
            "dependencies": self.dependencies,
            "config": self.config,
        }


class SkillTemplateManager:
    """Manager for skill templates."""

    # Predefined templates
    TEMPLATES = {
        "basic_python": SkillTemplate(
            name="Basic Python Skill",
            description="A basic Python skill template with standard structure",
            content="""name: {{skill_name}}
version: {{version}}
description: {{description}}
author: {{author}}
maintainer: {{author}}

# Skill metadata
keywords: {{keywords}}
category: {{category}}

# Requirements
python_requires: ">=3.8"
dependencies:
{{dependencies}}

# Skill configuration
config:
  enabled: true
  timeout: 30
  max_retries: 3

# Skill implementation
implementation:
  main_function: "{{skill_name_lower}}"
  entry_point: "main"

# Documentation
readme: |
  # {{skill_name}}

  {{description}}

  ## Installation

  ```bash
  pip install {{skill_name_lower}}
  ```

  ## Usage

  ```python
  from {{skill_name_lower}} import main

  result = main()
  ```
""",
            content_format="yaml",
            keywords=["python", "skill", "template"],
            dependencies=["click", "pydantic"],
            config={"enabled": True, "timeout": 30},
        ),

        "data_processing": SkillTemplate(
            name="Data Processing Skill",
            description="A template for data processing skills with pandas and numpy",
            content="""name: {{skill_name}}
version: {{version}}
description: {{description}}
author: {{author}}

# Skill metadata
keywords: ["data", "processing", "pandas", "numpy", "analysis"]
category: "data-processing"

# Requirements
python_requires: ">=3.8"
dependencies:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - jupyter

# Configuration
config:
  enabled: true
  data_dir: "./data"
  output_dir: "./output"
  cache_enabled: true
  memory_limit: "4GB"

# Data schemas
schemas:
  input:
    type: object
    properties:
      data_file:
        type: string
        description: "Path to input data file"
      format:
        type: string
        enum: ["csv", "json", "xlsx"]
        default: "csv"

  output:
    type: object
    properties:
      result_file:
        type: string
        description: "Path to output file"
      summary_stats:
        type: boolean
        default: true

# Implementation
implementation:
  main_function: "process_data"
  validate_input: true
  generate_report: true

# Documentation
readme: |
  # {{skill_name}}

  Data processing skill for analyzing and transforming datasets.

  ## Features

  - Multiple input formats (CSV, JSON, Excel)
  - Data validation and cleaning
  - Statistical analysis
  - Visualization generation
  - Report creation

  ## Usage

  ```python
  from {{skill_name_lower}} import DataProcessor

  processor = DataProcessor()
  results = processor.process("data.csv")
  ```
""",
            content_format="yaml",
            keywords=["data", "processing", "pandas", "numpy", "analysis"],
            dependencies=["pandas", "numpy", "matplotlib", "seaborn"],
            config={
                "enabled": True,
                "data_dir": "./data",
                "output_dir": "./output",
                "cache_enabled": True,
            },
        ),

        "api_service": SkillTemplate(
            name="API Service Skill",
            description="A template for building API service skills with FastAPI",
            content="""name: {{skill_name}}
version: {{version}}
description: {{description}}
author: {{author}}

# Skill metadata
keywords: ["api", "fastapi", "web", "service"]
category: "api-service"

# Requirements
python_requires: ">=3.8"
dependencies:
  - fastapi
  - uvicorn
  - pydantic
  - sqlalchemy
  - alembic
  - redis

# Configuration
config:
  host: "0.0.0.0"
  port: 8000
  debug: false
  workers: 1
  database_url: "sqlite:///./app.db"
  redis_url: "redis://localhost:6379"

# API endpoints
endpoints:
  - path: "/health"
    method: "GET"
    description: "Health check endpoint"

  - path: "/predict"
    method: "POST"
    description: "Prediction endpoint"
    request_model: "PredictionRequest"
    response_model: "PredictionResponse"

# Models
models:
  PredictionRequest:
    type: object
    properties:
      input_data:
        type: string
        description: "Input data for prediction"

  PredictionResponse:
    type: object
    properties:
      prediction:
        type: string
        confidence:
          type: number
          minimum: 0
          maximum: 1

# Implementation
implementation:
  framework: "fastapi"
  async_support: true
  middleware:
    - cors
    - authentication
    - logging
""",
            content_format="yaml",
            keywords=["api", "fastapi", "web", "service"],
            dependencies=["fastapi", "uvicorn", "pydantic", "sqlalchemy"],
            config={
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "workers": 1,
            },
        ),

        "ml_model": SkillTemplate(
            name="Machine Learning Model Skill",
            description="A template for machine learning model skills with scikit-learn",
            content="""name: {{skill_name}}
version: {{version}}
description: {{description}}
author: {{author}}

# Skill metadata
keywords: ["machine-learning", "scikit-learn", "model", "prediction"]
category: "machine-learning"

# Requirements
python_requires: ">=3.8"
dependencies:
  - scikit-learn
  - pandas
  - numpy
  - joblib
  - matplotlib
  - seaborn

# Configuration
config:
  model_path: "./models"
  cache_dir: "./cache"
  random_state: 42
  cross_validation_folds: 5
  test_size: 0.2

# Model specification
model:
  type: "classifier"  # classifier, regressor, clusterer
  algorithm: "RandomForest"  # RandomForest, SVM, NeuralNetwork, etc.
  hyperparameters:
    n_estimators: 100
    max_depth: 10
    random_state: 42

# Data schema
data:
  features:
    type: array
    items:
      type: number
    description: "Feature vector"
  target:
    type: string
    description: "Target variable"

# Training configuration
training:
  batch_size: 1000
  epochs: 100
  validation_split: 0.2
  early_stopping: true
  save_model: true

# Prediction API
prediction:
  endpoint: "/predict"
  method: "POST"
  request_format: "json"
  response_format: "json"

# Implementation
implementation:
  framework: "scikit-learn"
  pipeline: true
  preprocessing: true
  feature_engineering: true
""",
            content_format="yaml",
            keywords=["machine-learning", "scikit-learn", "model", "prediction"],
            dependencies=["scikit-learn", "pandas", "numpy", "joblib", "matplotlib"],
            config={
                "model_path": "./models",
                "cache_dir": "./cache",
                "random_state": 42,
            },
        ),

        "cli_tool": SkillTemplate(
            name="CLI Tool Skill",
            description="A template for command-line interface tools with Click",
            content="""name: {{skill_name}}
version: {{version}}
description: {{description}}
author: {{author}}

# Skill metadata
keywords: ["cli", "command-line", "click", "tool"]
category: "cli-tool"

# Requirements
python_requires: ">=3.8"
dependencies:
  - click
  - typer
  - rich
  - pyyaml

# Configuration
config:
  name: "{{skill_name_lower}}"
  version: "{{version}}"
  description: "{{description}}"
  help_option: true
  verbose: false

# CLI commands
commands:
  - name: "process"
    description: "Process data"
    options:
      - name: "input"
        type: "file"
        required: true
        help: "Input file path"
      - name: "output"
        type: "file"
        required: true
        help: "Output file path"
      - name: "format"
        type: "choice"
        choices: ["json", "csv", "yaml"]
        default: "json"
        help: "Output format"
      - name: "verbose"
        is_flag: true
        help: "Enable verbose output"

  - name: "validate"
    description: "Validate input data"
    options:
      - name: "schema"
        type: "file"
        required: true
        help: "Schema file path"
      - name: "data"
        type: "file"
        required: true
        help: "Data file path"

# Implementation
implementation:
  framework: "click"
  async_support: false
  color_output: true
  progress_bars: true

# Usage examples
examples:
  - |
    # Process CSV file
    {{skill_name_lower}} process input.csv output.json --format json --verbose
  - |
    # Validate data
    {{skill_name_lower}} validate schema.yaml data.csv
""",
            content_format="yaml",
            keywords=["cli", "command-line", "click", "tool"],
            dependencies=["click", "typer", "rich", "pyyaml"],
            config={
                "name": "{{skill_name_lower}}",
                "help_option": True,
                "verbose": False,
            },
        ),

        "web_scraper": SkillTemplate(
            name="Web Scraper Skill",
            description="A template for web scraping skills with BeautifulSoup and requests",
            content="""name: {{skill_name}}
version: {{version}}
description: {{description}}
author: {{author}}

# Skill metadata
keywords: ["scraping", "web", "requests", "beautifulsoup"]
category: "web-scraper"

# Requirements
python_requires: ">=3.8"
dependencies:
  - requests
  - beautifulsoup4
  - lxml
  - selenium
  - pandas

# Configuration
config:
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  request_delay: 1.0
  timeout: 30
  retry_attempts: 3
  max_pages: 100
  use_selenium: false
  headless: true

# Scraping rules
scraping:
  base_url: "{{base_url}}"
  selectors:
    title: "h1, .title, #title"
    content: ".content, .article, #content"
    links: "a"
    images: "img"
    date: "time, .date, #date"

  pagination:
    enabled: true
    next_selector: ".next, .pagination-next, a[rel='next']"
    max_pages: 10

  rate_limiting:
    delay: 1.0
    max_requests_per_minute: 60

# Data extraction
extraction:
  fields:
    - name: "title"
      selector: "h1"
      required: true

    - name: "content"
      selector: ".content"
      required: false

    - name: "date"
      selector: "time"
      type: "datetime"
      required: false

    - name: "author"
      selector: ".author"
      required: false

# Output configuration
output:
  format: "json"
  file_path: "./scraped_data.json"
  encoding: "utf-8"
  indent: 2

# Implementation
implementation:
  framework: "requests + BeautifulSoup"
  error_handling: true
  logging: true
  progress_tracking: true
""",
            content_format="yaml",
            keywords=["scraping", "web", "requests", "beautifulsoup"],
            dependencies=["requests", "beautifulsoup4", "lxml", "pandas"],
            config={
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "request_delay": 1.0,
                "timeout": 30,
                "retry_attempts": 3,
            },
        ),
    }

    @classmethod
    def get_template(cls, template_name: str) -> Optional[SkillTemplate]:
        """Get template by name.

        Args:
            template_name: Name of template

        Returns:
            SkillTemplate instance or None
        """
        return cls.TEMPLATES.get(template_name)

    @classmethod
    def list_templates(cls) -> List[Dict[str, str]]:
        """List all available templates.

        Returns:
            List of template information
        """
        return [
            {
                "name": template.name,
                "description": template.description,
                "keywords": template.keywords,
                "dependencies": template.dependencies,
            }
            for template in cls.TEMPLATES.values()
        ]

    @classmethod
    def render_template(
        cls,
        template_name: str,
        variables: Dict[str, Any],
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Render template with variables.

        Args:
            template_name: Name of template
            variables: Variables to substitute

        Returns:
            Tuple of (success, rendered_content, error_message)
        """
        template = cls.get_template(template_name)
        if not template:
            return False, None, f"Template '{template_name}' not found"

        try:
            rendered = template.render(variables)
            return True, rendered, None
        except Exception as e:
            return False, None, f"Failed to render template: {str(e)}"

    @classmethod
    def create_skill_from_template(
        cls,
        template_name: str,
        skill_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create skill data from template.

        Args:
            template_name: Name of template
            skill_data: Base skill data

        Returns:
            Complete skill data
        """
        template = cls.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Create skill data
        skill = {
            "name": skill_data.get("name", "New Skill"),
            "description": skill_data.get("description", template.description),
            "version": skill_data.get("version", template.version),
            "author": skill_data.get("author", "Unknown"),
            "keywords": skill_data.get("keywords", template.keywords),
            "dependencies": skill_data.get("dependencies", template.dependencies),
            "config": skill_data.get("config", template.config),
            "content": skill_data.get("content", template.content),
            "content_format": skill_data.get("content_format", template.content_format),
        }

        # Add template metadata
        skill["_template_used"] = template_name
        skill["_template_description"] = template.description

        return skill


class TemplateValidator:
    """Validator for skill templates."""

    @staticmethod
    def validate_template(template: SkillTemplate) -> Tuple[bool, List[str]]:
        """Validate template structure.

        Args:
            template: Template to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not template.name:
            errors.append("Template name is required")

        if not template.description:
            errors.append("Template description is required")

        if not template.content:
            errors.append("Template content is required")

        # Validate content format
        if template.content_format not in ["yaml", "json", "python", "text"]:
            errors.append(f"Unsupported content format: {template.content_format}")

        # Check for required variables in content
        required_vars = ["{{skill_name}}", "{{version}}", "{{description}}"]
        for var in required_vars:
            if var not in template.content:
                errors.append(f"Required variable not found in content: {var}")

        # Validate dependencies
        if template.dependencies:
            for dep in template.dependencies:
                if not re.match(r"^[a-zA-Z0-9\-_.]+", dep):
                    errors.append(f"Invalid dependency format: {dep}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_variables(template: SkillTemplate, variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate template variables.

        Args:
            template: Template to validate against
            variables: Variables to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Extract required variables from content
        var_pattern = r"\{\{(\w+)\}\}"
        required_vars = set(re.findall(var_pattern, template.content))

        # Check for missing variables
        for var in required_vars:
            if var not in variables:
                errors.append(f"Required variable not provided: {var}")

        return len(errors) == 0, errors


class TemplateRenderer:
    """Advanced template renderer with conditional logic and loops."""

    @staticmethod
    def render_advanced(template_content: str, variables: Dict[str, Any]) -> str:
        """Render template with advanced features.

        Args:
            template_content: Template content with advanced syntax
            variables: Variables dictionary

        Returns:
            Rendered content
        """
        content = template_content

        # Process conditional blocks {% if condition %}
        if_pattern = r"\{\%\s*if\s+([^%]+)\s*\%\}(.*?)\{\%\s*endif\s*\%\}"

        def replace_if_block(match):
            condition = match.group(1).strip()
            block_content = match.group(2)

            # Simple condition evaluation
            try:
                # Replace variables in condition
                for var, value in variables.items():
                    condition = condition.replace(var, str(value))

                # Evaluate condition (basic implementation)
                result = eval(condition, {"__builtins__": {}}, {})

                if result:
                    return TemplateRenderer.render_advanced(block_content, variables)
                else:
                    return ""
            except:
                return block_content  # On error, include the block

        content = re.sub(if_pattern, replace_if_block, content, flags=re.DOTALL)

        # Process loops {% for item in list %}
        for_pattern = r"\{\%\s*for\s+(\w+)\s+in\s+([^%]+)\s*\%\}(.*?)\{\%\s*endfor\s*\%\}"

        def replace_for_block(match):
            item_var = match.group(1)
            list_var = match.group(2).strip()
            block_content = match.group(3)

            try:
                # Get list from variables
                list_value = variables.get(list_var, [])

                if isinstance(list_value, list):
                    rendered_blocks = []
                    for item in list_value:
                        item_vars = variables.copy()
                        item_vars[item_var] = item
                        rendered_blocks.append(
                            TemplateRenderer.render_advanced(block_content, item_vars)
                        )
                    return "".join(rendered_blocks)
                else:
                    return ""
            except:
                return ""

        content = re.sub(for_pattern, replace_for_block, content, flags=re.DOTALL)

        # Process simple variable replacements
        var_pattern = r"\{\{(\w+)(?::([^}]+))?\}\}"

        def replace_var(match):
            var_name = match.group(1)
            filter_name = match.group(2)

            value = variables.get(var_name, "")

            # Apply filters
            if filter_name:
                if filter_name == "upper":
                    value = str(value).upper()
                elif filter_name == "lower":
                    value = str(value).lower()
                elif filter_name == "title":
                    value = str(value).title()
                elif filter_name == "default":
                    default_val = match.group(2).split(":")[1] if ":" in match.group(2) else ""
                    value = value or default_val

            return str(value)

        content = re.sub(var_pattern, replace_var, content)

        return content
