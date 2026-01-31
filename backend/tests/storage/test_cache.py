"""Tests for CacheManager.

This module contains unit tests for the CacheManager class,
testing all cache operations with mocked Redis connections.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json

try:
    from redis.asyncio import Redis
    from redis.exceptions import RedisError, ConnectionError, TimeoutError
except ImportError:
    Redis = None
    RedisError = Exception
    ConnectionError = Exception
    TimeoutError = Exception

from backend.app.storage.cache import (
    CacheManager,
    CacheError,
    CacheConnectionError,
    CacheOperationError,
)
from backend.app.storage.cache import CacheError as CacheErrorBase


class TestCacheManager:
    """Test suite for CacheManager."""

    @pytest.fixture
    def cache_manager(self):
        """Create CacheManager instance."""
        return CacheManager(
            redis_url="redis://localhost:6379",
            database=0,
            max_connections=20,
            default_ttl=3600,
            max_cache_size=10000,
            lru_cleanup_threshold=0.8,
            enable_stats=True,
        )

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return Mock(spec=Redis)

    @pytest.fixture
    def test_data(self):
        """Create test data."""
        return {
            "string": "test string",
            "number": 42,
            "float": 3.14,
            "dict": {"key": "value", "nested": {"a": 1}},
            "list": [1, 2, 3, "four"],
            "uuid": str(uuid4()),
            "datetime": datetime.utcnow().isoformat(),
        }

    # Test initialization
    @pytest.mark.asyncio
    async def test_initialization(self, cache_manager):
        """Test cache manager initialization."""
        assert cache_manager.redis_url == "redis://localhost:6379"
        assert cache_manager.database == 0
        assert cache_manager.max_connections == 20
        assert cache_manager.default_ttl == 3600
        assert cache_manager.max_cache_size == 10000
        assert cache_manager.lru_cleanup_threshold == 0.8
        assert cache_manager.enable_stats is True

    @pytest.mark.asyncio
    async def test_initialize_success(self, cache_manager, mock_redis):
        """Test successful cache initialization."""
        # Mock Redis connection
        mock_redis.ping.return_value = True
        cache_manager._redis_pool = mock_redis

        await cache_manager.initialize()

        assert cache_manager._redis_pool is not None
        mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, cache_manager):
        """Test cache initialization failure."""
        with patch("backend.app.storage.cache.redis", None):
            with pytest.raises(CacheConnectionError):
                await cache_manager.initialize()

    @pytest.mark.asyncio
    async def test_close(self, cache_manager, mock_redis):
        """Test cache manager close."""
        cache_manager._redis_pool = mock_redis

        await cache_manager.close()

        assert cache_manager._redis_pool is None
        mock_redis.close.assert_called_once()

    # Test cache operations
    @pytest.mark.asyncio
    async def test_set_success(self, cache_manager, mock_redis, test_data):
        """Test successful cache set."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        result = await cache_manager.set("test_key", test_data)

        assert result is True
        mock_redis.setex.assert_called_once()
        assert mock_redis.setex.call_args[0][0].startswith("file:")  # Default prefix
        assert mock_redis.setex.call_args[0][1] == 3600  # Default TTL

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_manager, mock_redis, test_data):
        """Test cache set with custom TTL."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        result = await cache_manager.set("test_key", test_data, ttl=7200, prefix="version")

        assert result is True
        assert mock_redis.setex.call_args[0][1] == 7200
        assert mock_redis.setex.call_args[0][0].startswith("version:")

    @pytest.mark.asyncio
    async def test_set_redis_error(self, cache_manager, mock_redis, test_data):
        """Test cache set with Redis error."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.side_effect = RedisError("Redis error")

        with pytest.raises(CacheOperationError):
            await cache_manager.set("test_key", test_data)

    @pytest.mark.asyncio
    async def test_get_success(self, cache_manager, mock_redis, test_data):
        """Test successful cache get."""
        cache_manager._redis_pool = mock_redis

        # Mock serialized data
        serialized_data = json.dumps(test_data)
        mock_redis.get.return_value = serialized_data.encode("utf-8")

        result = await cache_manager.get("test_key")

        assert result == test_data
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_manager, mock_redis):
        """Test cache get with miss."""
        cache_manager._redis_pool = mock_redis
        mock_redis.get.return_value = None

        result = await cache_manager.get("nonexistent_key", default="default_value")

        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_get_redis_error(self, cache_manager, mock_redis):
        """Test cache get with Redis error."""
        cache_manager._redis_pool = mock_redis
        mock_redis.get.side_effect = RedisError("Redis error")

        with pytest.raises(CacheOperationError):
            await cache_manager.get("test_key")

    @pytest.mark.asyncio
    async def test_delete_success(self, cache_manager, mock_redis):
        """Test successful cache delete."""
        cache_manager._redis_pool = mock_redis
        mock_redis.delete.return_value = 1

        result = await cache_manager.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, cache_manager, mock_redis):
        """Test cache delete with key not found."""
        cache_manager._redis_pool = mock_redis
        mock_redis.delete.return_value = 0

        result = await cache_manager.delete("nonexistent_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_success(self, cache_manager, mock_redis):
        """Test cache exists check."""
        cache_manager._redis_pool = mock_redis
        mock_redis.exists.return_value = 1

        result = await cache_manager.exists("test_key")

        assert result is True
        mock_redis.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_not_found(self, cache_manager, mock_redis):
        """Test cache exists with key not found."""
        cache_manager._redis_pool = mock_redis
        mock_redis.exists.return_value = 0

        result = await cache_manager.exists("nonexistent_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_expire_success(self, cache_manager, mock_redis):
        """Test cache expire set."""
        cache_manager._redis_pool = mock_redis
        mock_redis.expire.return_value = 1

        result = await cache_manager.expire("test_key", 3600)

        assert result is True
        mock_redis.expire.assert_called_once_with("file:test_key", 3600)

    @pytest.mark.asyncio
    async def test_get_ttl(self, cache_manager, mock_redis):
        """Test cache TTL get."""
        cache_manager._redis_pool = mock_redis
        mock_redis.ttl.return_value = 3600

        result = await cache_manager.get_ttl("test_key")

        assert result == 3600
        mock_redis.ttl.assert_called_once_with("file:test_key")

    @pytest.mark.asyncio
    async def test_clear_prefix(self, cache_manager, mock_redis):
        """Test cache clear by prefix."""
        cache_manager._redis_pool = mock_redis
        mock_redis.keys.return_value = ["file:key1", "file:key2"]
        mock_redis.delete.return_value = 2

        result = await cache_manager.clear_prefix("file")

        assert result == 2
        mock_redis.keys.assert_called_once_with("file:*")
        mock_redis.delete.assert_called_once_with("file:key1", "file:key2")

    # Test file-specific cache operations
    @pytest.mark.asyncio
    async def test_cache_file_metadata(self, cache_manager, mock_redis):
        """Test file metadata caching."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        skill_id = uuid4()
        file_path = "test.txt"
        metadata = {"size": 1024, "type": "text/plain"}

        result = await cache_manager.cache_file_metadata(skill_id, file_path, metadata)

        assert result is True
        assert mock_redis.setex.called

    @pytest.mark.asyncio
    async def test_get_cached_file_metadata(self, cache_manager, mock_redis):
        """Test get cached file metadata."""
        cache_manager._redis_pool = mock_redis

        skill_id = uuid4()
        file_path = "test.txt"
        metadata = {"size": 1024, "type": "text/plain"}
        serialized_metadata = json.dumps(metadata)
        mock_redis.get.return_value = serialized_metadata.encode("utf-8")

        result = await cache_manager.get_cached_file_metadata(skill_id, file_path)

        assert result == metadata

    @pytest.mark.asyncio
    async def test_cache_version_info(self, cache_manager, mock_redis):
        """Test version info caching."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        skill_id = uuid4()
        file_path = "test.txt"
        version_info = [
            {"version": 1, "date": "2024-01-01"},
            {"version": 2, "date": "2024-01-02"},
        ]

        result = await cache_manager.cache_version_info(skill_id, file_path, version_info)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_cached_version_info(self, cache_manager, mock_redis):
        """Test get cached version info."""
        cache_manager._redis_pool = mock_redis

        skill_id = uuid4()
        file_path = "test.txt"
        version_info = [
            {"version": 1, "date": "2024-01-01"},
            {"version": 2, "date": "2024-01-02"},
        ]
        serialized_version_info = json.dumps(version_info)
        mock_redis.get.return_value = serialized_version_info.encode("utf-8")

        result = await cache_manager.get_cached_version_info(skill_id, file_path)

        assert result == version_info

    @pytest.mark.asyncio
    async def test_cache_skill_stats(self, cache_manager, mock_redis):
        """Test skill statistics caching."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        skill_id = uuid4()
        stats = {"file_count": 10, "total_size": 2048}

        result = await cache_manager.cache_skill_stats(skill_id, stats)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_cached_skill_stats(self, cache_manager, mock_redis):
        """Test get cached skill statistics."""
        cache_manager._redis_pool = mock_redis

        skill_id = uuid4()
        stats = {"file_count": 10, "total_size": 2048}
        serialized_stats = json.dumps(stats)
        mock_redis.get.return_value = serialized_stats.encode("utf-8")

        result = await cache_manager.get_cached_skill_stats(skill_id)

        assert result == stats

    @pytest.mark.asyncio
    async def test_invalidate_file_cache_specific(self, cache_manager, mock_redis):
        """Test invalidate specific file cache."""
        cache_manager._redis_pool = mock_redis
        mock_redis.delete.return_value = 1

        skill_id = uuid4()
        file_path = "test.txt"

        result = await cache_manager.invalidate_file_cache(skill_id, file_path)

        assert result == 1

    @pytest.mark.asyncio
    async def test_invalidate_file_cache_all(self, cache_manager, mock_redis):
        """Test invalidate all files for skill."""
        cache_manager._redis_pool = mock_redis
        mock_redis.keys.return_value = ["file:skill1:file1", "file:skill1:file2"]
        mock_redis.delete.return_value = 2

        skill_id = uuid4()

        result = await cache_manager.invalidate_file_cache(skill_id)

        assert result == 2

    # Test cache warming
    @pytest.mark.asyncio
    async def test_warm_cache(self, cache_manager, mock_redis):
        """Test cache warming."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        skill_ids = [uuid4(), uuid4()]
        file_paths = ["test1.txt", "test2.txt"]

        result = await cache_manager.warm_cache(skill_ids, file_paths)

        assert "skills_warmed" in result
        assert "files_warmed" in result
        assert result["skills_warmed"] == 2
        assert result["files_warmed"] == 4  # 2 skills * 2 files

    @pytest.mark.asyncio
    async def test_warm_cache_partial(self, cache_manager, mock_redis):
        """Test cache warming with only skill IDs."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        skill_ids = [uuid4()]

        result = await cache_manager.warm_cache(skill_ids)

        assert result["skills_warmed"] == 1
        assert result["files_warmed"] == 0

    # Test statistics
    @pytest.mark.asyncio
    async def test_get_statistics(self, cache_manager, mock_redis):
        """Test cache statistics retrieval."""
        cache_manager._redis_pool = mock_redis

        # Mock Redis info
        mock_redis.info.return_value = {
            "connected_clients": 5,
            "used_memory_human": "1MB",
            "used_memory_peak_human": "2MB",
            "db0": {"keys": 100},
            "memory": {},
        }

        # Trigger some cache operations
        cache_manager.stats["hits"] = 80
        cache_manager.stats["misses"] = 20

        result = await cache_manager.get_statistics()

        assert "hits" in result
        assert "misses" in result
        assert "hit_rate_percent" in result
        assert result["hit_rate_percent"] == 80.0  # 80/100 * 100
        assert result["total_keys"] == 100

    @pytest.mark.asyncio
    async def test_reset_statistics(self, cache_manager):
        """Test statistics reset."""
        cache_manager.stats["hits"] = 100
        cache_manager.stats["misses"] = 50

        await cache_manager.reset_statistics()

        assert cache_manager.stats["hits"] == 0
        assert cache_manager.stats["misses"] == 0

    # Test health check
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, cache_manager, mock_redis):
        """Test health check when healthy."""
        cache_manager._redis_pool = mock_redis

        # Mock ping
        mock_redis.ping.return_value = True

        # Mock set/get
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = json.dumps({"timestamp": datetime.utcnow().isoformat()}).encode("utf-8")

        # Mock delete
        mock_redis.delete.return_value = 1

        result = await cache_manager.health_check()

        assert result["status"] == "healthy"
        assert result["ping_time_ms"] > 0
        assert result["read_write_test"] == "passed"
        assert result["connected"] is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, cache_manager, mock_redis):
        """Test health check when unhealthy."""
        cache_manager._redis_pool = mock_redis
        mock_redis.ping.side_effect = Exception("Connection failed")

        result = await cache_manager.health_check()

        assert result["status"] == "unhealthy"
        assert result["connected"] is False

    # Test LRU and eviction
    @pytest.mark.asyncio
    async def test_update_lru(self, cache_manager, mock_redis):
        """Test LRU tracking update."""
        cache_manager._redis_pool = mock_redis
        mock_redis.zadd.return_value = True
        mock_redis.expire.return_value = True

        await cache_manager._update_lru("file:test_key", "file")

        mock_redis.zadd.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_from_lru(self, cache_manager, mock_redis):
        """Test LRU tracking removal."""
        cache_manager._redis_pool = mock_redis
        mock_redis.zrem.return_value = True

        await cache_manager._remove_from_lru("file:test_key", "file")

        mock_redis.zrem.assert_called_once_with("lru:files", "file:test_key")

    @pytest.mark.asyncio
    async def test_check_cache_size_eviction(self, cache_manager, mock_redis):
        """Test cache size check with eviction."""
        cache_manager._redis_pool = mock_redis

        # Mock keys to exceed threshold
        mock_redis.keys.return_value = [f"file:key{i}" for i in range(9000)]
        mock_redis.zrange.return_value = [f"file:key{i}" for i in range(1000)]
        mock_redis.delete.return_value = 1000
        mock_redis.zrem.return_value = True

        await cache_manager._check_cache_size("file")

        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_cache_size_no_eviction(self, cache_manager, mock_redis):
        """Test cache size check without eviction."""
        cache_manager._redis_pool = mock_redis

        # Mock keys below threshold
        mock_redis.keys.return_value = [f"file:key{i}" for i in range(5000)]

        await cache_manager._check_cache_size("file")

        mock_redis.delete.assert_not_called()

    # Test error handling
    @pytest.mark.asyncio
    async def test_get_redis_not_initialized(self, cache_manager):
        """Test get Redis when not initialized."""
        with pytest.raises(CacheConnectionError):
            await cache_manager._get_redis()

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, cache_manager, mock_redis):
        """Test connection error handling."""
        cache_manager._redis_pool = mock_redis
        mock_redis.get.side_effect = ConnectionError("Connection failed")

        with pytest.raises(CacheOperationError):
            await cache_manager.get("test_key")

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, cache_manager, mock_redis):
        """Test timeout error handling."""
        cache_manager._redis_pool = mock_redis
        mock_redis.get.side_effect = TimeoutError("Timeout")

        with pytest.raises(CacheOperationError):
            await cache_manager.get("test_key")

    # Test serialization
    def test_serialize_string(self, cache_manager):
        """Test string serialization."""
        result = cache_manager._serialize("test string")
        assert json.loads(result) == "test string"

    def test_serialize_number(self, cache_manager):
        """Test number serialization."""
        result = cache_manager._serialize(42)
        assert json.loads(result) == 42

    def test_serialize_dict(self, cache_manager):
        """Test dictionary serialization."""
        test_dict = {"key": "value"}
        result = cache_manager._serialize(test_dict)
        assert json.loads(result) == test_dict

    def test_deserialize_string(self, cache_manager):
        """Test string deserialization."""
        result = cache_manager._deserialize("test string")
        assert result == "test string"

    def test_deserialize_bytes(self, cache_manager):
        """Test bytes deserialization."""
        result = cache_manager._deserialize(b'{"key": "value"}')
        assert result == {"key": "value"}

    # Test key generation
    def test_generate_file_key(self, cache_manager):
        """Test file key generation."""
        skill_id = uuid4()
        file_path = "test/subdir/file.txt"

        result = cache_manager._generate_file_key(skill_id, file_path)

        assert str(skill_id) in result
        assert "test/subdir/file.txt" in result

    # Test cache operation context manager
    @pytest.mark.asyncio
    async def test_cache_operation_context_success(self, cache_manager):
        """Test cache operation context manager success."""
        async with cache_manager.cache_operation("test_operation"):
            # Do nothing
            pass

    @pytest.mark.asyncio
    async def test_cache_operation_context_failure(self, cache_manager):
        """Test cache operation context manager with failure."""
        with pytest.raises(ValueError):
            async with cache_manager.cache_operation("test_operation"):
                raise ValueError("Test error")

    # Test integration scenarios
    @pytest.mark.asyncio
    async def test_full_cache_workflow(self, cache_manager, mock_redis, test_data):
        """Test complete cache workflow: set -> get -> update -> delete."""
        cache_manager._redis_pool = mock_redis

        # Mock responses
        mock_redis.setex.return_value = True
        serialized_data = json.dumps(test_data)
        mock_redis.get.side_effect = [
            None,  # First get (miss)
            serialized_data.encode("utf-8"),  # Second get (hit)
        ]
        mock_redis.delete.return_value = 1

        # 1. Set value
        result = await cache_manager.set("test_key", test_data)
        assert result is True

        # 2. Get value (cache miss)
        result = await cache_manager.get("test_key", default="default")
        assert result == test_data

        # 3. Get value (cache hit)
        result = await cache_manager.get("test_key")
        assert result == test_data

        # 4. Update value
        updated_data = {**test_data, "updated": True}
        result = await cache_manager.set("test_key", updated_data)
        assert result is True

        # 5. Delete value
        result = await cache_manager.delete("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_statistics_tracking(self, cache_manager, mock_redis):
        """Test cache statistics tracking."""
        cache_manager._redis_pool = mock_redis

        # Mock responses
        mock_redis.setex.return_value = True
        mock_redis.get.side_effect = [None, b'"cached"']

        # Perform operations
        await cache_manager.set("key1", "value1")  # Set
        await cache_manager.get("key1")  # Miss
        await cache_manager.get("key2")  # Miss
        await cache_manager.get("key1")  # Hit

        # Check statistics
        assert cache_manager.stats["sets"] == 1
        assert cache_manager.stats["misses"] == 2
        assert cache_manager.stats["hits"] == 1

        # Check hit rate
        total_requests = cache_manager.stats["hits"] + cache_manager.stats["misses"]
        hit_rate = (cache_manager.stats["hits"] / total_requests * 100)
        assert hit_rate == 33.33  # 1/3 * 100

    @pytest.mark.asyncio
    async def test_cache_with_disabled_stats(self, cache_manager, mock_redis):
        """Test cache with statistics disabled."""
        cache_manager.enable_stats = False
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        await cache_manager.set("test_key", "value")

        # Statistics should not be updated
        assert cache_manager.stats["sets"] == 0

    # Test configuration validation
    def test_cache_manager_configuration(self):
        """Test CacheManager with different configurations."""
        # Test with custom configuration
        cache_manager = CacheManager(
            redis_url="redis://localhost:6380",
            database=1,
            max_connections=50,
            default_ttl=7200,
            max_cache_size=20000,
            lru_cleanup_threshold=0.9,
            enable_stats=False,
        )

        assert cache_manager.redis_url == "redis://localhost:6380"
        assert cache_manager.database == 1
        assert cache_manager.max_connections == 50
        assert cache_manager.default_ttl == 7200
        assert cache_manager.max_cache_size == 20000
        assert cache_manager.lru_cleanup_threshold == 0.9
        assert cache_manager.enable_stats is False

    # Test invalid prefix handling
    @pytest.mark.asyncio
    async def test_invalid_prefix(self, cache_manager, mock_redis):
        """Test cache operation with invalid prefix."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        # Should work with valid prefix
        result = await cache_manager.set("test_key", "value", prefix="file")
        assert result is True

    # Test edge cases
    @pytest.mark.asyncio
    async def test_cache_with_none_value(self, cache_manager, mock_redis):
        """Test cache operation with None value."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        result = await cache_manager.set("test_key", None)

        assert result is True

    @pytest.mark.asyncio
    async def test_cache_with_large_data(self, cache_manager, mock_redis):
        """Test cache with large data."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True

        large_data = {"data": "x" * 100000}  # 100KB

        result = await cache_manager.set("test_key", large_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_cache_ttl_edge_cases(self, cache_manager, mock_redis):
        """Test cache TTL edge cases."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True
        mock_redis.ttl.return_value = 0
        mock_redis.expire.return_value = True

        # Test with zero TTL (should use default)
        await cache_manager.set("test_key", "value", ttl=0)

        # Test with negative TTL (should use default)
        await cache_manager.set("test_key", "value", ttl=-1)

        # Test TTL update
        await cache_manager.expire("test_key", 3600)

    # Test concurrent operations simulation
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self, cache_manager, mock_redis):
        """Test simulated concurrent cache operations."""
        cache_manager._redis_pool = mock_redis
        mock_redis.setex.return_value = True
        mock_redis.get.side_effect = [None, b'"value"']

        # Simulate concurrent operations
        tasks = [
            cache_manager.set(f"key{i}", f"value{i}")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert all(results)
        assert mock_redis.setex.call_count == 10
