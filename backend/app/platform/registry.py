"""Platform registry for managing platform adapters.

This module provides PlatformRegistry class for registering, discovering,
loading, and managing platform adapters.
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
import importlib
import inspect
import os
from pathlib import Path

from .adapters.base import PlatformAdapter, PlatformCapability
from .adapters import (
    ValidationError,
    ConfigurationError,
    PlatformError,
)

logger = logging.getLogger(__name__)


class PlatformRegistry:
    """Registry for managing platform adapters.

    Provides registration, discovery, loading, and management
    of platform adapters with thread-safe operations.
    """

    def __init__(self):
        """Initialize the platform registry."""
        self._adapters: Dict[str, Type[PlatformAdapter]] = {}
        self._instances: Dict[str, PlatformAdapter] = {}
        self._lock = threading.RLock()
        self._initialized = False
        self._discovery_paths = []

    # Registration Methods
    def register_adapter(
        self,
        adapter_class: Type[PlatformAdapter],
        platform_id: Optional[str] = None
    ) -> bool:
        """Register a platform adapter class.

        Args:
            adapter_class: Platform adapter class to register
            platform_id: Optional platform ID (defaults to adapter's platform_id)

        Returns:
            True if registration successful, False otherwise

        Raises:
            TypeError: If adapter_class is not a valid PlatformAdapter subclass
        """
        if not inspect.isclass(adapter_class):
            raise TypeError("Adapter must be a class")

        if not issubclass(adapter_class, PlatformAdapter):
            raise TypeError("Adapter must be subclass of PlatformAdapter")

        # Create temporary instance to get platform_id
        try:
            temp_adapter = adapter_class()
            actual_platform_id = platform_id or temp_adapter.platform_id
        except Exception as e:
            logger.error(f"Failed to create temporary adapter: {str(e)}")
            raise ConfigurationError(
                f"Cannot determine platform ID for adapter: {str(e)}",
                platform=adapter_class.__name__
            )

        with self._lock:
            if actual_platform_id in self._adapters:
                logger.warning(f"Overriding existing adapter for platform: {actual_platform_id}")

            self._adapters[actual_platform_id] = adapter_class
            logger.info(f"Registered adapter for platform: {actual_platform_id}")

            # Clear any cached instances
            if actual_platform_id in self._instances:
                del self._instances[actual_platform_id]

            return True

    def unregister_adapter(self, platform_id: str) -> bool:
        """Unregister a platform adapter.

        Args:
            platform_id: Platform ID to unregister

        Returns:
            True if unregistration successful, False if not found
        """
        with self._lock:
            if platform_id not in self._adapters:
                return False

            del self._adapters[platform_id]

            # Clean up cached instance
            if platform_id in self._instances:
                instance = self._instances[platform_id]
                try:
                    if hasattr(instance, 'cleanup'):
                        import asyncio
                        asyncio.create_task(instance.cleanup())
                except Exception as e:
                    logger.warning(f"Failed to cleanup adapter instance: {str(e)}")
                del self._instances[platform_id]

            logger.info(f"Unregistered adapter for platform: {platform_id}")
            return True

    def is_registered(self, platform_id: str) -> bool:
        """Check if platform adapter is registered.

        Args:
            platform_id: Platform ID to check

        Returns:
            True if registered, False otherwise
        """
        with self._lock:
            return platform_id in self._adapters

    def get_registered_platforms(self) -> List[str]:
        """Get list of registered platform IDs.

        Returns:
            List of registered platform IDs
        """
        with self._lock:
            return list(self._adapters.keys())

    # Discovery and Loading Methods
    def discover_adapters(
        self,
        package_path: Union[str, Path],
        recursive: bool = True
    ) -> int:
        """Discover and register adapters from a package path.

        Args:
            package_path: Path to package directory
            recursive: Whether to search recursively

        Returns:
            Number of adapters discovered and registered
        """
        discovered_count = 0
        package_path = Path(package_path)

        if not package_path.exists():
            logger.warning(f"Package path does not exist: {package_path}")
            return 0

        logger.info(f"Discovering adapters in: {package_path}")

        # Add to discovery paths for future reference
        with self._lock:
            if str(package_path) not in [str(p) for p in self._discovery_paths]:
                self._discovery_paths.append(package_path)

        try:
            # Import the package
            spec = importlib.util.spec_from_file_location(
                "platform_adapters", package_path / "__init__.py"
            )

            if spec is None or spec.loader is None:
                logger.warning(f"Cannot load package: {package_path}")
                return 0

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all adapter classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, PlatformAdapter)
                    and obj != PlatformAdapter
                    and not getattr(obj, '__abstract__', False)
                ):
                    try:
                        self.register_adapter(obj)
                        discovered_count += 1
                        logger.info(f"Discovered adapter: {name}")
                    except Exception as e:
                        logger.error(f"Failed to register adapter {name}: {str(e)}")

            # Search subdirectories if recursive
            if recursive:
                for subdir in package_path.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('__'):
                        discovered_count += self.discover_adapters(subdir, recursive=False)

        except Exception as e:
            logger.error(f"Error discovering adapters: {str(e)}")

        logger.info(f"Discovered {discovered_count} adapters in {package_path}")
        return discovered_count

    def load_adapter(
        self,
        platform_id: str,
        config: Optional[Dict[str, Any]] = None,
        force_reload: bool = False
    ) -> Optional[PlatformAdapter]:
        """Load a platform adapter instance.

        Args:
            platform_id: Platform ID to load
            config: Adapter configuration
            force_reload: Whether to force reload even if cached

        Returns:
            Loaded adapter instance or None if not found

        Raises:
            PlatformError: If loading fails
        """
        with self._lock:
            # Check if already loaded and not forcing reload
            if not force_reload and platform_id in self._instances:
                return self._instances[platform_id]

            # Check if adapter is registered
            if platform_id not in self._adapters:
                raise PlatformError(
                    f"Adapter not found for platform: {platform_id}",
                    error_code="ADAPTER_NOT_FOUND",
                    platform=platform_id
                )

            adapter_class = self._adapters[platform_id]

            try:
                # Create new instance
                instance = adapter_class(config=config)

                # Initialize the adapter
                if hasattr(instance, 'initialize'):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        success = loop.run_until_complete(instance.initialize())
                        if not success:
                            raise ConfigurationError(
                                f"Failed to initialize adapter for platform: {platform_id}",
                                platform=platform_id
                            )
                    finally:
                        loop.close()

                # Cache the instance
                self._instances[platform_id] = instance

                logger.info(f"Loaded adapter for platform: {platform_id}")
                return instance

            except Exception as e:
                logger.error(f"Failed to load adapter for {platform_id}: {str(e)}")
                raise PlatformError(
                    f"Failed to load adapter: {str(e)}",
                    error_code="LOAD_FAILED",
                    platform=platform_id,
                    details={"error": str(e)}
                )

    def unload_adapter(self, platform_id: str) -> bool:
        """Unload a platform adapter instance.

        Args:
            platform_id: Platform ID to unload

        Returns:
            True if unloaded successfully, False if not found
        """
        with self._lock:
            if platform_id not in self._instances:
                return False

            instance = self._instances[platform_id]

            try:
                # Cleanup the instance
                if hasattr(instance, 'cleanup'):
                    import asyncio
                    asyncio.create_task(instance.cleanup())

                del self._instances[platform_id]
                logger.info(f"Unloaded adapter for platform: {platform_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to unload adapter for {platform_id}: {str(e)}")
                return False

    def get_adapter(
        self,
        platform_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[PlatformAdapter]:
        """Get a platform adapter instance (load if necessary).

        Args:
            platform_id: Platform ID to get
            config: Optional configuration for new instances

        Returns:
            Adapter instance or None if not found
        """
        with self._lock:
            # Return cached instance if available
            if platform_id in self._instances:
                return self._instances[platform_id]

            # Try to load if registered
            if platform_id in self._adapters:
                return self.load_adapter(platform_id, config)

            return None

    def get_all_adapters(self) -> Dict[str, PlatformAdapter]:
        """Get all loaded adapter instances.

        Returns:
            Dictionary of platform_id to adapter instances
        """
        with self._lock:
            return self._instances.copy()

    # Management Methods
    def clear_all(self) -> None:
        """Clear all registered adapters and instances."""
        with self._lock:
            # Cleanup all instances
            for platform_id in list(self._instances.keys()):
                self.unload_adapter(platform_id)

            # Clear registrations
            self._adapters.clear()

            logger.info("Cleared all platform adapters and instances")

    def reload_all(self) -> Dict[str, bool]:
        """Reload all adapter instances.

        Returns:
            Dictionary of platform_id to reload success status
        """
        results = {}

        with self._lock:
            platform_ids = list(self._instances.keys())

        for platform_id in platform_ids:
            try:
                config = None
                old_instance = self._instances.get(platform_id)
                if old_instance:
                    config = old_instance.config

                self.unload_adapter(platform_id)
                self.load_adapter(platform_id, config)
                results[platform_id] = True

            except Exception as e:
                logger.error(f"Failed to reload adapter for {platform_id}: {str(e)}")
                results[platform_id] = False

        return results

    def validate_all(self) -> Dict[str, Dict[str, Any]]:
        """Validate configuration for all registered adapters.

        Returns:
            Dictionary of platform_id to validation results
        """
        results = {}

        for platform_id in self.get_registered_platforms():
            try:
                adapter = self.get_adapter(platform_id)
                if adapter and hasattr(adapter, 'validate_configuration'):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        validation_result = loop.run_until_complete(
                            adapter.validate_configuration()
                        )
                        results[platform_id] = validation_result
                    finally:
                        loop.close()
                else:
                    results[platform_id] = {"valid": False, "errors": ["No validate_configuration method"]}

            except Exception as e:
                results[platform_id] = {
                    "valid": False,
                    "errors": [str(e)]
                }
                logger.error(f"Validation failed for {platform_id}: {str(e)}")

        return results

    # Information Methods
    def get_registry_info(self) -> Dict[str, Any]:
        """Get registry information.

        Returns:
            Registry information dictionary
        """
        with self._lock:
            return {
                "registered_platforms": len(self._adapters),
                "loaded_instances": len(self._instances),
                "platforms": list(self._adapters.keys()),
                "loaded_platforms": list(self._instances.keys()),
                "discovery_paths": [str(p) for p in self._discovery_paths],
                "initialized": self._initialized,
            }

    def get_platform_info(self, platform_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive platform information.

        Args:
            platform_id: Platform ID

        Returns:
            Platform information or None if not found
        """
        adapter = self.get_adapter(platform_id)
        if not adapter:
            return None

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                platform_info = loop.run_until_complete(
                    adapter.get_platform_info()
                )
                return {
                    "platform_id": adapter.platform_id,
                    "display_name": adapter.display_name,
                    "platform_type": adapter.platform_type,
                    "supported_formats": adapter.supported_formats,
                    "max_file_size": adapter.max_file_size,
                    "features": adapter.features,
                    "capabilities": adapter.capabilities,
                    "adapter_version": adapter.adapter_version,
                    "platform_version": adapter.platform_version,
                    "is_initialized": adapter.is_initialized,
                    "is_loaded": True,
                    "platform_info": platform_info,
                }
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Failed to get platform info for {platform_id}: {str(e)}")
            return None

    def search_platforms(
        self,
        query: str,
        search_fields: Optional[List[str]] = None
    ) -> List[str]:
        """Search for platforms by query.

        Args:
            query: Search query string
            search_fields: Fields to search in

        Returns:
            List of matching platform IDs
        """
        if not search_fields:
            search_fields = ["platform_id", "display_name", "platform_type"]

        matches = []

        for platform_id in self.get_registered_platforms():
            adapter = self.get_adapter(platform_id)
            if not adapter:
                continue

            query_lower = query.lower()

            # Search in specified fields
            for field in search_fields:
                if field == "platform_id" and query_lower in adapter.platform_id.lower():
                    matches.append(platform_id)
                    break
                elif field == "display_name" and query_lower in adapter.display_name.lower():
                    matches.append(platform_id)
                    break
                elif field == "platform_type" and query_lower in adapter.platform_type.lower():
                    matches.append(platform_id)
                    break

        return matches

    # Thread Safety
    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.clear_all()


# Global registry instance
_global_registry = PlatformRegistry()


def get_registry() -> PlatformRegistry:
    """Get the global platform registry instance.

    Returns:
        Global PlatformRegistry instance
    """
    return _global_registry


def register_adapter(adapter_class: Type[PlatformAdapter]) -> bool:
    """Register an adapter with the global registry.

    Args:
        adapter_class: Adapter class to register

    Returns:
        True if registration successful
    """
    return _global_registry.register_adapter(adapter_class)


def get_adapter(
    platform_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[PlatformAdapter]:
    """Get an adapter from the global registry.

    Args:
        platform_id: Platform ID
        config: Optional configuration

    Returns:
        Adapter instance or None
    """
    return _global_registry.get_adapter(platform_id, config)


def get_registered_platforms() -> List[str]:
    """Get list of registered platforms.

    Returns:
        List of registered platform IDs
    """
    return _global_registry.get_registered_platforms()