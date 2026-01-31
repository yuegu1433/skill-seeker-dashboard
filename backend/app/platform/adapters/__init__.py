"""Platform adapters package.

This package contains platform-specific adapters for different LLM platforms,
providing unified interfaces for platform operations.
"""

from .base import (
    PlatformAdapter,
    PlatformCapability,
    PlatformError,
    ValidationError,
    ConversionError,
    DeploymentError,
    ConfigurationError,
    RateLimitError,
    UnsupportedFormatError,
    FileSizeError,
)

# Import platform adapters
from .claude_adapter import ClaudeAdapter
from .gemini_adapter import GeminiAdapter
from .openai_adapter import OpenAIAdapter
from .markdown_adapter import MarkdownAdapter

__all__ = [
    "PlatformAdapter",
    "PlatformCapability",
    "PlatformError",
    "ValidationError",
    "ConversionError",
    "DeploymentError",
    "ConfigurationError",
    "RateLimitError",
    "UnsupportedFormatError",
    "FileSizeError",
    "ClaudeAdapter",
    "GeminiAdapter",
    "OpenAIAdapter",
    "MarkdownAdapter",
]