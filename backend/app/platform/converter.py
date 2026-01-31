"""Format converter for multi-platform skill format conversion.

This module provides FormatConverter class that implements unified
format conversion engine with multi-platform support.
"""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime
import yaml

from .registry import get_registry
from .adapters import (
    PlatformAdapter,
    ValidationError,
    ConversionError,
    PlatformError,
)

logger = logging.getLogger(__name__)


class FormatConverter:
    """Unified format converter for multi-platform skill format conversion.

    Provides efficient format conversion capabilities across multiple platforms
    with support for concurrent operations and caching.
    """

    def __init__(self, registry: Optional[PlatformAdapter] = None):
        """Initialize format converter.

        Args:
            registry: Platform registry instance (uses global if None)
        """
        self.registry = registry or get_registry()
        self.conversion_cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Conversion statistics
        self.stats = {
            "total_conversions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_conversion_time": 0.0
        }

        # Supported conversion paths
        self.conversion_paths = self._init_conversion_paths()

        # Register event handlers
        self.event_handlers = {
            "conversion_start": [],
            "conversion_complete": [],
            "conversion_error": []
        }

    def _init_conversion_paths(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """Initialize conversion paths configuration.

        Returns:
            Conversion paths configuration
        """
        return {
            # JSON conversions
            ("json", "yaml"): {
                "method": "json_to_yaml",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("json", "claude"): {
                "method": "json_to_claude",
                "platform": "claude",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("json", "gemini"): {
                "method": "json_to_gemini",
                "platform": "gemini",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("json", "openai"): {
                "method": "json_to_openai",
                "platform": "openai",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("json", "markdown"): {
                "method": "json_to_markdown",
                "platform": "markdown",
                "supports_bidirectional": True,
                "priority": 1
            },

            # YAML conversions
            ("yaml", "json"): {
                "method": "yaml_to_json",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("yaml", "claude"): {
                "method": "yaml_to_claude",
                "platform": "claude",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("yaml", "gemini"): {
                "method": "yaml_to_gemini",
                "platform": "gemini",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("yaml", "openai"): {
                "method": "yaml_to_openai",
                "platform": "openai",
                "supports_bidirectional": True,
                "priority": 1
            },
            ("yaml", "markdown"): {
                "method": "yaml_to_markdown",
                "platform": "markdown",
                "supports_bidirectional": True,
                "priority": 1
            },

            # Platform-specific conversions
            ("claude", "gemini"): {
                "method": "claude_to_gemini",
                "via": "json",
                "priority": 2
            },
            ("claude", "openai"): {
                "method": "claude_to_openai",
                "via": "json",
                "priority": 2
            },
            ("claude", "markdown"): {
                "method": "claude_to_markdown",
                "via": "json",
                "priority": 2
            },
            ("gemini", "openai"): {
                "method": "gemini_to_openai",
                "via": "json",
                "priority": 2
            },
            ("gemini", "markdown"): {
                "method": "gemini_to_markdown",
                "via": "json",
                "priority": 2
            },
            ("openai", "markdown"): {
                "method": "openai_to_markdown",
                "via": "json",
                "priority": 2
            }
        }

    async def convert(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str,
        platform_id: Optional[str] = None,
        conversion_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert skill from source format to target format.

        Args:
            skill_data: Source skill data
            source_format: Source format
            target_format: Target format
            platform_id: Optional platform ID for platform-specific conversion
            conversion_config: Optional conversion configuration

        Returns:
            Converted skill data with metadata

        Raises:
            ValidationError: If skill data is invalid
            ConversionError: If conversion fails
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(skill_data, source_format, target_format, platform_id)

        # Check cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            self.stats["cache_hits"] += 1
            logger.info(f"Cache hit for conversion: {source_format} -> {target_format}")
            return cached_result

        self.stats["cache_misses"] += 1
        self.stats["total_conversions"] += 1

        # Emit conversion start event
        await self._emit_event("conversion_start", {
            "source_format": source_format,
            "target_format": target_format,
            "platform_id": platform_id
        })

        try:
            # Validate input
            await self._validate_conversion_input(skill_data, source_format, target_format)

            # Check if direct conversion is possible
            conversion_path = self._find_conversion_path(source_format, target_format)

            if not conversion_path:
                raise ConversionError(
                    f"No conversion path found from {source_format} to {target_format}",
                    source_format=source_format,
                    target_format=target_format
                )

            # Perform conversion
            if "via" in conversion_path:
                # Multi-step conversion
                result = await self._convert_via_intermediate(
                    skill_data,
                    source_format,
                    target_format,
                    conversion_path["via"],
                    conversion_config
                )
            else:
                # Direct conversion
                result = await self._convert_direct(
                    skill_data,
                    source_format,
                    target_format,
                    platform_id,
                    conversion_config
                )

            # Add conversion metadata
            conversion_time = time.time() - start_time
            result["conversion_metadata"] = {
                "source_format": source_format,
                "target_format": target_format,
                "platform_id": platform_id,
                "conversion_time": conversion_time,
                "timestamp": datetime.utcnow().isoformat(),
                "conversion_path": conversion_path.get("method", "direct")
            }

            # Cache result
            self._cache_result(cache_key, result)

            # Update statistics
            self.stats["successful_conversions"] += 1
            self._update_avg_conversion_time(conversion_time)

            # Emit conversion complete event
            await self._emit_event("conversion_complete", {
                "source_format": source_format,
                "target_format": target_format,
                "conversion_time": conversion_time
            })

            logger.info(
                f"Conversion completed: {source_format} -> {target_format} "
                f"in {conversion_time:.3f}s"
            )
            return result

        except Exception as e:
            # Update statistics
            self.stats["failed_conversions"] += 1

            # Emit conversion error event
            await self._emit_event("conversion_error", {
                "source_format": source_format,
                "target_format": target_format,
                "error": str(e)
            })

            logger.error(f"Conversion failed: {str(e)}")
            raise

    async def convert_batch(
        self,
        conversions: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Convert multiple skills concurrently.

        Args:
            conversions: List of conversion requests
            max_concurrent: Maximum concurrent conversions

        Returns:
            List of conversion results

        Raises:
            ConversionError: If batch conversion fails
        """
        logger.info(f"Starting batch conversion of {len(conversions)} items")

        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []

        for conversion in conversions:
            task = self._convert_with_semaphore(
                semaphore,
                conversion,
                self.convert
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_results = []
        failed_results = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "index": i,
                    "error": str(result),
                    "success": False
                })
            else:
                result["success"] = True
                successful_results.append(result)

        logger.info(
            f"Batch conversion completed: {len(successful_results)} successful, "
            f"{len(failed_results)} failed"
        )

        return successful_results + failed_results

    async def validate_conversion(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str,
        platform_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate if conversion is possible.

        Args:
            skill_data: Skill data to validate
            source_format: Source format
            target_format: Target format
            platform_id: Optional platform ID

        Returns:
            Validation result
        """
        validation_result = {
            "valid": False,
            "source_format": source_format,
            "target_format": target_format,
            "platform_id": platform_id,
            "errors": [],
            "warnings": [],
            "conversion_path": None
        }

        try:
            # Check if conversion path exists
            conversion_path = self._find_conversion_path(source_format, target_format)
            if not conversion_path:
                validation_result["errors"].append(
                    f"No conversion path from {source_format} to {target_format}"
                )
                return validation_result

            validation_result["conversion_path"] = conversion_path

            # Validate source format
            if source_format in ["json", "yaml"]:
                await self._validate_standard_format(skill_data, source_format, validation_result)
            else:
                await self._validate_platform_format(skill_data, source_format, platform_id, validation_result)

            # Check if target format is supported
            if target_format not in self.get_supported_formats():
                validation_result["warnings"].append(
                    f"Target format {target_format} may not be fully supported"
                )

            # Determine validity
            validation_result["valid"] = len(validation_result["errors"]) == 0

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False

        return validation_result

    def get_supported_formats(self) -> Set[str]:
        """Get set of supported formats.

        Returns:
            Set of supported format names
        """
        formats = set()

        # Add standard formats
        formats.update(["json", "yaml", "markdown"])

        # Add platform-specific formats
        for platform_id in self.registry.get_registered_platforms():
            adapter = self.registry.get_adapter(platform_id)
            if adapter:
                formats.update(adapter.supported_formats)

        return formats

    def get_conversion_paths(self, source_format: str, target_format: str) -> List[Dict[str, Any]]:
        """Get available conversion paths between formats.

        Args:
            source_format: Source format
            target_format: Target format

        Returns:
            List of conversion paths
        """
        paths = []

        # Direct path
        direct_path = self.conversion_paths.get((source_format, target_format))
        if direct_path:
            paths.append({
                "type": "direct",
                "method": direct_path["method"],
                "priority": direct_path["priority"]
            })

        # Multi-step paths
        intermediate_formats = ["json", "yaml"]
        for intermediate in intermediate_formats:
            path1 = self.conversion_paths.get((source_format, intermediate))
            path2 = self.conversion_paths.get((intermediate, target_format))

            if path1 and path2:
                total_priority = path1["priority"] + path2["priority"]
                paths.append({
                    "type": "via_intermediate",
                    "intermediate": intermediate,
                    "path1": path1["method"],
                    "path2": path2["method"],
                    "priority": total_priority
                })

        # Sort by priority
        paths.sort(key=lambda x: x["priority"])

        return paths

    def get_conversion_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()

        # Calculate success rate
        if stats["total_conversions"] > 0:
            stats["success_rate"] = (
                stats["successful_conversions"] / stats["total_conversions"] * 100
            )
        else:
            stats["success_rate"] = 0.0

        # Calculate cache hit rate
        total_cache_requests = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_requests > 0:
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / total_cache_requests * 100
            )
        else:
            stats["cache_hit_rate"] = 0.0

        return stats

    def clear_cache(self) -> None:
        """Clear conversion cache."""
        self.conversion_cache.clear()
        logger.info("Conversion cache cleared")

    def add_conversion_rule(
        self,
        source_format: str,
        target_format: str,
        rule_config: Dict[str, Any]
    ) -> None:
        """Add custom conversion rule.

        Args:
            source_format: Source format
            target_format: Target format
            rule_config: Rule configuration
        """
        self.conversion_paths[(source_format, target_format)] = rule_config
        logger.info(
            f"Added conversion rule: {source_format} -> {target_format}"
        )

    # Private methods

    def _generate_cache_key(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str,
        platform_id: Optional[str] = None
    ) -> str:
        """Generate cache key for conversion.

        Args:
            skill_data: Skill data
            source_format: Source format
            target_format: Target format
            platform_id: Platform ID

        Returns:
            Cache key string
        """
        # Create hash of skill data
        data_str = json.dumps(skill_data, sort_keys=True)
        import hashlib
        data_hash = hashlib.md5(data_str.encode()).hexdigest()

        # Create cache key
        key_parts = [
            source_format,
            target_format,
            platform_id or "none",
            data_hash
        ]
        return ":".join(key_parts)

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None
        """
        if cache_key not in self.conversion_cache:
            return None

        cache_entry = self.conversion_cache[cache_key]

        # Check TTL
        if time.time() - cache_entry["timestamp"] > self.cache_ttl:
            del self.conversion_cache[cache_key]
            return None

        return cache_entry["result"]

    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache conversion result.

        Args:
            cache_key: Cache key
            result: Conversion result
        """
        self.conversion_cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }

        # Clean up expired entries if cache is large
        if len(self.conversion_cache) > 1000:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.conversion_cache.items()
                if current_time - entry["timestamp"] > self.cache_ttl
            ]
            for key in expired_keys:
                del self.conversion_cache[key]

    def _find_conversion_path(
        self,
        source_format: str,
        target_format: str
    ) -> Optional[Dict[str, Any]]:
        """Find conversion path between formats.

        Args:
            source_format: Source format
            target_format: Target format

        Returns:
            Conversion path configuration or None
        """
        return self.conversion_paths.get((source_format, target_format))

    async def _validate_conversion_input(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str
    ) -> None:
        """Validate conversion input.

        Args:
            skill_data: Skill data
            source_format: Source format
            target_format: Target format

        Raises:
            ValidationError: If validation fails
        """
        if not skill_data or not isinstance(skill_data, dict):
            raise ValidationError(
                "Skill data must be a non-empty dictionary",
                platform="converter"
            )

        if not source_format or not target_format:
            raise ValidationError(
                "Source and target formats are required",
                platform="converter"
            )

        supported_formats = self.get_supported_formats()
        if source_format not in supported_formats:
            raise ValidationError(
                f"Unsupported source format: {source_format}",
                platform="converter"
            )

        if target_format not in supported_formats:
            raise ValidationError(
                f"Unsupported target format: {target_format}",
                platform="converter"
            )

    async def _convert_direct(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str,
        platform_id: Optional[str],
        conversion_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform direct conversion.

        Args:
            skill_data: Source skill data
            source_format: Source format
            target_format: Target format
            platform_id: Platform ID
            conversion_config: Conversion configuration

        Returns:
            Converted data
        """
        # If platform-specific conversion
        if platform_id:
            adapter = self.registry.get_adapter(platform_id)
            if not adapter:
                raise ConversionError(
                    f"Adapter not found for platform: {platform_id}",
                    platform_id=platform_id
                )

            # Use adapter's conversion method
            if hasattr(adapter, "convert_skill"):
                return await adapter.convert_skill(skill_data, source_format, target_format)
            else:
                # Fallback to internal conversion
                return await self._convert_with_adapter(skill_data, source_format, target_format, adapter)

        # Standard format conversion
        return await self._convert_standard_formats(skill_data, source_format, target_format)

    async def _convert_via_intermediate(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str,
        intermediate_format: str,
        conversion_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convert via intermediate format.

        Args:
            skill_data: Source skill data
            source_format: Source format
            target_format: Target format
            intermediate_format: Intermediate format
            conversion_config: Conversion configuration

        Returns:
            Converted data
        """
        # Step 1: Convert to intermediate
        intermediate_data = await self.convert(
            skill_data,
            source_format,
            intermediate_format,
            conversion_config=conversion_config
        )

        # Step 2: Convert intermediate to target
        result = await self.convert(
            intermediate_data,
            intermediate_format,
            target_format,
            conversion_config=conversion_config
        )

        return result

    async def _convert_with_adapter(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str,
        adapter: PlatformAdapter
    ) -> Dict[str, Any]:
        """Convert using platform adapter.

        Args:
            skill_data: Source skill data
            source_format: Source format
            target_format: Target format
            adapter: Platform adapter

        Returns:
            Converted data
        """
        if not hasattr(adapter, "convert_skill"):
            raise ConversionError(
                f"Adapter {adapter.platform_id} does not support conversion",
                platform_id=adapter.platform_id
            )

        return await adapter.convert_skill(skill_data, source_format, target_format)

    async def _convert_standard_formats(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str
    ) -> Dict[str, Any]:
        """Convert between standard formats (JSON, YAML, etc.).

        Args:
            skill_data: Source skill data
            source_format: Source format
            target_format: Target format

        Returns:
            Converted data
        """
        if source_format == "json" and target_format == "yaml":
            return {
                "data": yaml.safe_dump(skill_data, default_flow_style=False),
                "format": "yaml"
            }
        elif source_format == "yaml" and target_format == "json":
            return {
                "data": yaml.safe_load(json.dumps(skill_data)),
                "format": "json"
            }
        else:
            raise ConversionError(
                f"Unsupported standard format conversion: {source_format} -> {target_format}"
            )

    async def _convert_with_semaphore(
        self,
        conversion: Dict[str, Any],
        convert_func
    ) -> Dict[str, Any]:
        """Execute conversion with semaphore control.

        Args:
            conversion: Conversion request
            convert_func: Conversion function

        Returns:
            Conversion result
        """
        async with conversion["semaphore"]:
            return await convert_func(
                conversion["skill_data"],
                conversion["source_format"],
                conversion["target_format"],
                conversion.get("platform_id"),
                conversion.get("conversion_config")
            )

    def _update_avg_conversion_time(self, conversion_time: float) -> None:
        """Update average conversion time statistic.

        Args:
            conversion_time: Conversion time in seconds
        """
        total = self.stats["successful_conversions"]
        current_avg = self.stats["avg_conversion_time"]

        # Update running average
        self.stats["avg_conversion_time"] = (
            (current_avg * (total - 1) + conversion_time) / total
        )

    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit conversion event.

        Args:
            event_type: Event type
            event_data: Event data
        """
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.warning(f"Event handler error: {str(e)}")

    async def _validate_standard_format(
        self,
        skill_data: Dict[str, Any],
        format_type: str,
        validation_result: Dict[str, Any]
    ) -> None:
        """Validate standard format.

        Args:
            skill_data: Skill data
            format_type: Format type
            validation_result: Validation result to update
        """
        if format_type == "json":
            try:
                json.dumps(skill_data)
            except (TypeError, ValueError) as e:
                validation_result["errors"].append(f"Invalid JSON: {str(e)}")
        elif format_type == "yaml":
            try:
                yaml.safe_dump(skill_data)
            except Exception as e:
                validation_result["errors"].append(f"Invalid YAML: {str(e)}")

    async def _validate_platform_format(
        self,
        skill_data: Dict[str, Any],
        format_type: str,
        platform_id: Optional[str],
        validation_result: Dict[str, Any]
    ) -> None:
        """Validate platform-specific format.

        Args:
            skill_data: Skill data
            format_type: Format type
            platform_id: Platform ID
            validation_result: Validation result to update
        """
        # Delegate to platform adapter if available
        if platform_id:
            adapter = self.registry.get_adapter(platform_id)
            if adapter and hasattr(adapter, "validate_skill_format"):
                try:
                    result = await adapter.validate_skill_format(skill_data, format_type)
                    if not result["valid"]:
                        validation_result["errors"].extend(result.get("errors", []))
                        validation_result["warnings"].extend(result.get("warnings", []))
                except Exception as e:
                    validation_result["errors"].append(f"Platform validation error: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.executor.shutdown(wait=True)