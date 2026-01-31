"""CacheManager - Redis-based caching for MinIO storage.

This module provides the CacheManager class which manages Redis-based caching
for file metadata, version information, and frequently accessed data to improve
storage system performance.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    from redis.exceptions import RedisError, ConnectionError, TimeoutError
except ImportError:
    # Redis not installed - will be installed with dependencies
    Redis = None
    RedisError = Exception
    ConnectionError = Exception
    TimeoutError = Exception

from .utils.validators import validate_file_path, validate_skill_id
from .utils.formatters import format_file_size, format_timestamp

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache operations."""
    pass


class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""
    pass


class CacheOperationError(CacheError):
    """Raised when cache operation fails."""
    pass


class CacheKeyError(CacheError):
    """Raised when cache key is invalid."""
    pass


class CacheManager:
    """Redis-based cache manager for storage system.

    Provides high-performance caching for file metadata, version information,
    and frequently accessed data using Redis with TTL management and LRU cleanup.
    """

    def __init__(
        self,
        redis_url: str,
        database: int = 0,
        max_connections: int = 20,
        default_ttl: int = 3600,
        max_cache_size: int = 10000,
        lru_cleanup_threshold: int = 0.8,
        enable_stats: bool = True,
    ):
        """Initialize cache manager.

        Args:
            redis_url: Redis connection URL
            database: Redis database number
            max_connections: Maximum number of connections in pool
            default_ttl: Default TTL for cache entries (seconds)
            max_cache_size: Maximum number of cache entries
            lru_cleanup_threshold: Threshold for LRU cleanup (0.0-1.0)
            enable_stats: Whether to enable statistics collection
        """
        self.redis_url = redis_url
        self.database = database
        self.max_connections = max_connections
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.lru_cleanup_threshold = lru_cleanup_threshold
        self.enable_stats = enable_stats

        # Redis connection pool
        self._redis_pool: Optional[Redis] = None

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "errors": 0,
        }

        # Cache key prefixes
        self.prefixes = {
            "file": "file:",
            "version": "version:",
            "metadata": "meta:",
            "stats": "stats:",
            "skill": "skill:",
        }

        # LRU tracking sets
        self.lru_sets = {
            "file": "lru:files",
            "version": "lru:versions",
            "metadata": "lru:metadata",
        }

        logger.info(f"CacheManager initialized with Redis: {redis_url}")

    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        if Redis is None:
            raise CacheConnectionError("Redis client not installed")

        try:
            # Create connection pool
            self._redis_pool = redis.from_url(
                self.redis_url,
                db=self.database,
                max_connections=self.max_connections,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )

            # Test connection
            await self._redis_pool.ping()

            logger.info(f"CacheManager connected to Redis database {self.database}")

        except Exception as e:
            raise CacheConnectionError(f"Failed to connect to Redis: {e}")

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._redis_pool:
            await self._redis_pool.close()
            self._redis_pool = None
            logger.info("CacheManager connection closed")

    async def _get_redis(self) -> Redis:
        """Get Redis client from pool."""
        if self._redis_pool is None:
            raise CacheConnectionError("Cache manager not initialized")
        return self._redis_pool

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix: str = "file",
    ) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            prefix: Key prefix

        Returns:
            True if set successfully

        Raises:
            CacheConnectionError: If cache is not connected
            CacheOperationError: If operation fails
        """
        redis_client = await self._get_redis()

        try:
            # Apply prefix
            cache_key = f"{self.prefixes[prefix]}{key}"

            # Serialize value
            serialized_value = self._serialize(value)

            # Set TTL
            ttl = ttl or self.default_ttl

            # Set value in Redis
            await redis_client.setex(cache_key, ttl, serialized_value)

            # Update LRU tracking
            await self._update_lru(cache_key, prefix)

            # Check cache size and evict if necessary
            await self._check_cache_size(prefix)

            # Update statistics
            if self.enable_stats:
                self.stats["sets"] += 1

            logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")

            return True

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache set error for key {key}: {e}")
            if self.enable_stats:
                self.stats["errors"] += 1
            raise CacheOperationError(f"Cache set failed: {e}")

    async def get(
        self,
        key: str,
        prefix: str = "file",
        default: Any = None,
    ) -> Any:
        """Get a value from cache.

        Args:
            key: Cache key
            prefix: Key prefix
            default: Default value if key not found

        Returns:
            Cached value or default

        Raises:
            CacheConnectionError: If cache is not connected
        """
        redis_client = await self._get_redis()

        try:
            # Apply prefix
            cache_key = f"{self.prefixes[prefix]}{key}"

            # Get value from Redis
            serialized_value = await redis_client.get(cache_key)

            if serialized_value is None:
                # Cache miss
                if self.enable_stats:
                    self.stats["misses"] += 1
                logger.debug(f"Cache miss: {cache_key}")
                return default

            # Cache hit
            if self.enable_stats:
                self.stats["hits"] += 1

            # Update LRU tracking
            await self._update_lru(cache_key, prefix)

            # Deserialize value
            value = self._deserialize(serialized_value)

            logger.debug(f"Cache hit: {cache_key}")

            return value

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache get error for key {key}: {e}")
            if self.enable_stats:
                self.stats["errors"] += 1
            raise CacheOperationError(f"Cache get failed: {e}")

    async def delete(self, key: str, prefix: str = "file") -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key
            prefix: Key prefix

        Returns:
            True if deleted successfully

        Raises:
            CacheConnectionError: If cache is not connected
        """
        redis_client = await self._get_redis()

        try:
            # Apply prefix
            cache_key = f"{self.prefixes[prefix]}{key}"

            # Delete from Redis
            result = await redis_client.delete(cache_key)

            # Remove from LRU tracking
            await self._remove_from_lru(cache_key, prefix)

            # Update statistics
            if self.enable_stats and result:
                self.stats["deletes"] += 1

            logger.debug(f"Cache delete: {cache_key}")

            return bool(result)

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            if self.enable_stats:
                self.stats["errors"] += 1
            raise CacheOperationError(f"Cache delete failed: {e}")

    async def exists(self, key: str, prefix: str = "file") -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key
            prefix: Key prefix

        Returns:
            True if key exists

        Raises:
            CacheConnectionError: If cache is not connected
        """
        redis_client = await self._get_redis()

        try:
            # Apply prefix
            cache_key = f"{self.prefixes[prefix]}{key}"

            # Check existence
            result = await redis_client.exists(cache_key)

            logger.debug(f"Cache exists: {cache_key} -> {bool(result)}")

            return bool(result)

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            raise CacheOperationError(f"Cache exists check failed: {e}")

    async def expire(self, key: str, ttl: int, prefix: str = "file") -> bool:
        """Set TTL for a cache key.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds
            prefix: Key prefix

        Returns:
            True if TTL set successfully

        Raises:
            CacheConnectionError: If cache is not connected
        """
        redis_client = await self._get_redis()

        try:
            # Apply prefix
            cache_key = f"{self.prefixes[prefix]}{key}"

            # Set TTL
            result = await redis_client.expire(cache_key, ttl)

            logger.debug(f"Cache expire: {cache_key} -> {ttl}s")

            return bool(result)

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            raise CacheOperationError(f"Cache expire failed: {e}")

    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with a given prefix.

        Args:
            prefix: Key prefix

        Returns:
            Number of keys deleted

        Raises:
            CacheConnectionError: If cache is not connected
        """
        redis_client = await self._get_redis()

        try:
            # Get all keys with prefix
            pattern = f"{self.prefixes[prefix]}*"
            keys = await redis_client.keys(pattern)

            if keys:
                # Delete all keys
                result = await redis_client.delete(*keys)
                logger.info(f"Cache clear: {pattern} -> {result} keys deleted")
                return result
            else:
                logger.debug(f"Cache clear: {pattern} -> 0 keys (none found)")
                return 0

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache clear error for prefix {prefix}: {e}")
            raise CacheOperationError(f"Cache clear failed: {e}")

    async def get_ttl(self, key: str, prefix: str = "file") -> int:
        """Get TTL for a cache key.

        Args:
            key: Cache key
            prefix: Key prefix

        Returns:
            TTL in seconds (-1 if no TTL, -2 if key doesn't exist)

        Raises:
            CacheConnectionError: If cache is not connected
        """
        redis_client = await self._get_redis()

        try:
            # Apply prefix
            cache_key = f"{self.prefixes[prefix]}{key}"

            # Get TTL
            ttl = await redis_client.ttl(cache_key)

            logger.debug(f"Cache TTL: {cache_key} -> {ttl}s")

            return ttl

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            raise CacheOperationError(f"Cache TTL check failed: {e}")

    # File-specific cache operations

    async def cache_file_metadata(
        self,
        skill_id: UUID,
        file_path: str,
        metadata: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache file metadata.

        Args:
            skill_id: Skill ID
            file_path: File path
            metadata: File metadata
            ttl: Optional TTL override

        Returns:
            True if cached successfully
        """
        key = self._generate_file_key(skill_id, file_path)
        return await self.set(key, metadata, ttl=ttl, prefix="file")

    async def get_cached_file_metadata(
        self,
        skill_id: UUID,
        file_path: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached file metadata.

        Args:
            skill_id: Skill ID
            file_path: File path

        Returns:
            Cached metadata or None
        """
        key = self._generate_file_key(skill_id, file_path)
        return await self.get(key, prefix="file")

    async def cache_version_info(
        self,
        skill_id: UUID,
        file_path: str,
        version_info: List[Dict[str, Any]],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache version information.

        Args:
            skill_id: Skill ID
            file_path: File path
            version_info: Version information list
            ttl: Optional TTL override

        Returns:
            True if cached successfully
        """
        key = f"{skill_id}:{file_path}:versions"
        return await self.set(key, version_info, ttl=ttl, prefix="version")

    async def get_cached_version_info(
        self,
        skill_id: UUID,
        file_path: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached version information.

        Args:
            skill_id: Skill ID
            file_path: File path

        Returns:
            Cached version info or None
        """
        key = f"{skill_id}:{file_path}:versions"
        return await self.get(key, prefix="version")

    async def cache_skill_stats(
        self,
        skill_id: UUID,
        stats: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache skill statistics.

        Args:
            skill_id: Skill ID
            stats: Skill statistics
            ttl: Optional TTL override

        Returns:
            True if cached successfully
        """
        key = f"stats:{skill_id}"
        return await self.set(key, stats, ttl=ttl, prefix="stats")

    async def get_cached_skill_stats(
        self,
        skill_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get cached skill statistics.

        Args:
            skill_id: Skill ID

        Returns:
            Cached statistics or None
        """
        key = f"stats:{skill_id}"
        return await self.get(key, prefix="stats")

    async def invalidate_file_cache(
        self,
        skill_id: UUID,
        file_path: Optional[str] = None,
    ) -> int:
        """Invalidate file-related cache entries.

        Args:
            skill_id: Skill ID
            file_path: Optional specific file path (clears all if None)

        Returns:
            Number of cache entries invalidated
        """
        redis_client = await self._get_redis()

        try:
            if file_path:
                # Invalidate specific file
                file_key = self._generate_file_key(skill_id, file_path)
                version_key = f"{skill_id}:{file_path}:versions"

                count = 0
                count += await self.delete(file_key, prefix="file")
                count += await self.delete(version_key, prefix="version")

                logger.debug(f"Invalidated cache for file {file_path}: {count} entries")
                return count
            else:
                # Invalidate all files for skill
                pattern = f"{self.prefixes['file']}*{skill_id}*"
                keys = await redis_client.keys(pattern)
                if keys:
                    count = await redis_client.delete(*keys)
                    logger.info(f"Invalidated all cache for skill {skill_id}: {count} entries")
                    return count
                return 0

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache invalidation error: {e}")
            raise CacheOperationError(f"Cache invalidation failed: {e}")

    # Cache warming

    async def warm_cache(
        self,
        skill_ids: List[UUID],
        file_paths: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Warm up cache with frequently accessed data.

        Args:
            skill_ids: List of skill IDs to warm
            file_paths: Optional list of file paths to warm

        Returns:
            Dictionary with warming statistics
        """
        stats = {
            "skills_warmed": 0,
            "files_warmed": 0,
            "versions_warmed": 0,
            "errors": 0,
        }

        for skill_id in skill_ids:
            try:
                # Cache skill statistics (placeholder - would load from actual data source)
                skill_stats = {
                    "skill_id": str(skill_id),
                    "file_count": 0,
                    "total_size": 0,
                    "last_updated": datetime.utcnow().isoformat(),
                }
                await self.cache_skill_stats(skill_id, skill_stats)
                stats["skills_warmed"] += 1

                # Cache file metadata for each file path
                if file_paths:
                    for file_path in file_paths:
                        # Placeholder metadata
                        file_metadata = {
                            "skill_id": str(skill_id),
                            "file_path": file_path,
                            "file_size": 0,
                            "content_type": "application/octet-stream",
                            "last_modified": datetime.utcnow().isoformat(),
                        }
                        await self.cache_file_metadata(skill_id, file_path, file_metadata)
                        stats["files_warmed"] += 1

            except Exception as e:
                logger.error(f"Cache warming error for skill {skill_id}: {e}")
                stats["errors"] += 1

        logger.info(f"Cache warming completed: {stats}")
        return stats

    # Statistics

    async def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        redis_client = await self._get_redis()

        try:
            # Get Redis info
            redis_info = await redis_client.info()

            # Calculate hit rate
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            # Get memory usage
            memory_info = redis_info.get("memory", {})

            # Get key counts
            db_info = redis_info.get("db0", {})
            total_keys = db_info.get("keys", 0)

            statistics = {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate_percent": round(hit_rate, 2),
                "sets": self.stats["sets"],
                "deletes": self.stats["deletes"],
                "evictions": self.stats["evictions"],
                "errors": self.stats["errors"],
                "total_requests": total_requests,
                "redis_connected_clients": redis_info.get("connected_clients", 0),
                "redis_used_memory_human": redis_info.get("used_memory_human", "0B"),
                "redis_used_memory_peak_human": redis_info.get("used_memory_peak_human", "0B"),
                "total_keys": total_keys,
                "configuration": {
                    "default_ttl": self.default_ttl,
                    "max_cache_size": self.max_cache_size,
                    "lru_cleanup_threshold": self.lru_cleanup_threshold,
                    "enable_stats": self.enable_stats,
                },
            }

            logger.debug(f"Cache statistics: {statistics}")

            return statistics

        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Cache statistics error: {e}")
            raise CacheOperationError(f"Cache statistics failed: {e}")

    async def reset_statistics(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
            "errors": 0,
        }
        logger.info("Cache statistics reset")

    # Health check

    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check.

        Returns:
            Dictionary with health status
        """
        redis_client = await self._get_redis()

        try:
            # Test ping
            start_time = time.time()
            await redis_client.ping()
            ping_time = (time.time() - start_time) * 1000  # ms

            # Test write/read
            test_key = "health_check:test"
            test_value = {"timestamp": datetime.utcnow().isoformat()}
            await self.set(test_key, test_value, ttl=60)
            retrieved_value = await self.get(test_key)
            await self.delete(test_key)

            is_healthy = retrieved_value == test_value

            return {
                "status": "healthy" if is_healthy else "degraded",
                "ping_time_ms": round(ping_time, 2),
                "read_write_test": "passed" if is_healthy else "failed",
                "connected": True,
                "errors": 0,
            }

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "ping_time_ms": -1,
                "read_write_test": "failed",
                "connected": False,
                "errors": 1,
                "error_message": str(e),
            }

    # Private helper methods

    def _serialize(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        if isinstance(value, (str, int, float)):
            return json.dumps(value)
        else:
            return json.dumps(value, default=str)

    def _deserialize(self, value: Union[str, bytes]) -> Any:
        """Deserialize value from Redis storage."""
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def _generate_file_key(self, skill_id: UUID, file_path: str) -> str:
        """Generate cache key for file."""
        skill_id = validate_skill_id(skill_id)
        file_path = validate_file_path(file_path)
        return f"{skill_id}:{file_path}"

    async def _update_lru(self, key: str, cache_type: str) -> None:
        """Update LRU tracking for a key."""
        if cache_type not in self.lru_sets:
            return

        redis_client = await self._get_redis()
        lru_set = self.lru_sets[cache_type]

        try:
            # Add key to LRU set with timestamp
            await redis_client.zadd(lru_set, {key: time.time()})

            # Set TTL for LRU entry
            await redis_client.expire(lru_set, self.default_ttl * 2)

        except Exception as e:
            logger.warning(f"LRU update error: {e}")

    async def _remove_from_lru(self, key: str, cache_type: str) -> None:
        """Remove key from LRU tracking."""
        if cache_type not in self.lru_sets:
            return

        redis_client = await self._get_redis()
        lru_set = self.lru_sets[cache_type]

        try:
            await redis_client.zrem(lru_set, key)
        except Exception as e:
            logger.warning(f"LRU removal error: {e}")

    async def _check_cache_size(self, cache_type: str) -> None:
        """Check cache size and evict if necessary."""
        redis_client = await self._get_redis()

        try:
            # Get current cache size for this type
            pattern = f"{self.prefixes[cache_type]}*"
            keys = await redis_client.keys(pattern)
            current_size = len(keys)

            # Check if eviction is needed
            if current_size > self.max_cache_size * self.lru_cleanup_threshold:
                # Get LRU set for this cache type
                lru_set = self.lru_sets.get(cache_type)
                if lru_set:
                    # Get keys to evict (oldest 20%)
                    keys_to_evict = int(self.max_cache_size * 0.2)
                    lru_keys = await redis_client.zrange(lru_set, 0, keys_to_evict - 1)

                    if lru_keys:
                        # Delete evicted keys
                        deleted_count = await redis_client.delete(*lru_keys)
                        # Remove from LRU set
                        await redis_client.zrem(lru_set, *lru_keys)

                        # Update statistics
                        if self.enable_stats:
                            self.stats["evictions"] += deleted_count

                        logger.debug(f"Cache eviction: {deleted_count} keys removed from {cache_type}")

        except Exception as e:
            logger.warning(f"Cache size check error: {e}")

    @asynccontextmanager
    async def cache_operation(self, operation_name: str):
        """Context manager for cache operations.

        Args:
            operation_name: Name of operation
        """
        logger.debug(f"Starting cache operation: {operation_name}")
        start_time = time.time()

        try:
            yield
            duration = time.time() - start_time
            logger.debug(f"Cache operation '{operation_name}' completed in {duration:.3f}s")
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Cache operation '{operation_name}' failed after {duration:.3f}s: {e}")
            raise
