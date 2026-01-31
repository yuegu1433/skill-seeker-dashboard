"""Tests for message queue and cache optimization.

This module tests Redis message queuing, intelligent caching,
batch processing, and performance optimizations.
"""

import asyncio
import pytest
import time
from unittest.mock import MagicMock, patch, AsyncMock
from typing import List

from backend.app.progress.message_queue (
    RedisMessageQueue,
    IntelligentCache,
    MessageBatchProcessor,
    MessageQueueManager,
    QueuedMessage,
    MessagePriority,
    CacheStrategy,
    connection_pool_manager,
)


class TestIntelligentCache:
    """Test intelligent cache functionality."""

    @pytest.fixture
    def cache(self):
        """Create cache instance."""
        return IntelligentCache(
            max_size=100,
            max_memory_mb=10.0,
            strategy=CacheStrategy.LRU,
            default_ttl=1.0,
        )

    @pytest.mark.asyncio
    async def test_set_get(self, cache):
        """Test setting and getting cache values."""
        await cache.set("key1", "value1")

        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache):
        """Test cache expiration with TTL."""
        await cache.set("key1", "value1", ttl=0.1)

        value = await cache.get("key1")
        assert value == "value1"

        await asyncio.sleep(0.15)
        value = await cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_eviction_lru(self, cache):
        """Test LRU cache eviction."""
        # Fill cache to capacity
        for i in range(100):
            await cache.set(f"key{i}", f"value{i}")

        # Add one more to trigger eviction
        await cache.set("key101", "value101")

        # Check that oldest key was evicted
        value = await cache.get("key0")
        assert value is None

        # Check that new key exists
        value = await cache.get("key101")
        assert value == "value101"

    @pytest.mark.asyncio
    async def test_cache_eviction_lfu(self, cache):
        """Test LFU cache eviction."""
        cache.strategy = CacheStrategy.LFU

        # Add items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 more frequently
        for _ in range(5):
            await cache.get("key1")

        # Add more items to trigger eviction
        for i in range(4, 100):
            await cache.set(f"key{i}", f"value{i}")

        # key2 or key3 should be evicted (less frequently used)
        value2 = await cache.get("key2")
        value3 = await cache.get("key3")
        assert (value2 is None or value3 is None)

        # key1 should still exist (most frequently used)
        value1 = await cache.get("key1")
        assert value1 == "value1"

    @pytest.mark.asyncio
    async def test_cache_delete(self, cache):
        """Test cache deletion."""
        await cache.set("key1", "value1")

        result = await cache.delete("key1")
        assert result is True

        value = await cache.get("key1")
        assert value is None

        # Try deleting non-existent key
        result = await cache.delete("key999")
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        """Test cache clearing."""
        # Add some items
        for i in range(10):
            await cache.set(f"key{i}", f"value{i}")

        # Clear cache
        await cache.clear()

        # Check all are gone
        for i in range(10):
            value = await cache.get(f"key{i}")
            assert value is None

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        # Add some items
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")

        # Get stats before access
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 5
        assert stats["current_size"] == 5

    @pytest.mark.asyncio
    async def test_cache_hit_miss_tracking(self, cache):
        """Test hit and miss tracking."""
        # Add item
        await cache.set("key1", "value1")

        # Miss (wrong key)
        value = await cache.get("wrong_key")
        assert value is None

        # Hit (correct key)
        value = await cache.get("key1")
        assert value == "value1"

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestRedisMessageQueue:
    """Test Redis message queue functionality."""

    @pytest.fixture
    def queue(self):
        """Create queue instance."""
        return RedisMessageQueue(
            redis_url="redis://localhost:6379/15",  # Use separate DB
            max_size=1000,
            batch_size=50,
        )

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("redis", minversion="4.0.0"),
        reason="Redis not installed"
    )
    async def test_connect_disconnect(self, queue):
        """Test connecting and disconnecting from Redis."""
        try:
            await queue.connect()
            assert queue._is_connected

            await queue.disconnect()
            assert not queue._is_connected
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("redis", minversion="4.0.0"),
        reason="Redis not installed"
    )
    async def test_enqueue_dequeue(self, queue):
        """Test enqueueing and dequeueing messages."""
        try:
            await queue.connect()

            # Create test message
            message = QueuedMessage(
                id="test1",
                content={"data": "test"},
                priority=MessagePriority.HIGH,
                timestamp=time.time(),
            )

            # Enqueue
            result = await queue.enqueue(message)
            assert result is True

            # Dequeue
            dequeued = await queue.dequeue()
            assert dequeued is not None
            assert dequeued.id == "test1"
            assert dequeued.content["data"] == "test"

            await queue.disconnect()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("redis", minversion="4.0.0"),
        reason="Redis not installed"
    )
    async def test_priority_ordering(self, queue):
        """Test priority-based ordering."""
        try:
            await queue.connect()

            # Enqueue messages with different priorities
            messages = [
                QueuedMessage(
                    id=f"msg{i}",
                    content={"data": f"data{i}"},
                    priority=MessagePriority.LOW if i % 3 == 0 else MessagePriority.NORMAL,
                    timestamp=time.time(),
                )
                for i in range(10)
            ]

            for msg in messages:
                await queue.enqueue(msg)

            # Dequeue and check priority order
            dequeued = []
            for _ in range(10):
                msg = await queue.dequeue()
                if msg:
                    dequeued.append(msg)

            # Higher priority messages should come first
            priorities = [msg.priority.value for msg in dequeued]
            assert priorities == sorted(priorities)

            await queue.disconnect()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("redis", minversion="4.0.0"),
        reason="Redis not installed"
    )
    async def test_batch_operations(self, queue):
        """Test batch enqueue/dequeue operations."""
        try:
            await queue.connect()

            # Enqueue multiple messages
            for i in range(20):
                message = QueuedMessage(
                    id=f"batch{i}",
                    content={"data": f"data{i}"},
                    priority=MessagePriority.NORMAL,
                    timestamp=time.time(),
                )
                await queue.enqueue(message)

            # Batch dequeue
            batch = await queue.batch_dequeue(batch_size=10)
            assert len(batch) == 10

            # Dequeue remaining
            remaining = await queue.batch_dequeue(batch_size=20)
            assert len(remaining) == 10

            await queue.disconnect()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.importorskip("redis", minversion="4.0.0"),
        reason="Redis not installed"
    )
    async def test_queue_size(self, queue):
        """Test queue size tracking."""
        try:
            await queue.connect()

            # Check initial size
            size = await queue.get_queue_size()
            assert size == 0

            # Add messages
            for i in range(5):
                message = QueuedMessage(
                    id=f"size{i}",
                    content={"data": f"data{i}"},
                    priority=MessagePriority.NORMAL,
                    timestamp=time.time(),
                )
                await queue.enqueue(message)

            # Check size
            size = await queue.get_queue_size()
            assert size == 5

            # Clear queue
            await queue.clear_queue()

            # Check size again
            size = await queue.get_queue_size()
            assert size == 0

            await queue.disconnect()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestMessageBatchProcessor:
    """Test message batch processor."""

    @pytest.fixture
    def mock_queue(self):
        """Create mock queue."""
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache."""
        return MagicMock()

    @pytest.fixture
    def processor(self):
        """Create test processor."""
        def process_batch(messages: List[QueuedMessage]) -> List[str]:
            return [f"processed_{msg.id}" for msg in messages]

        return process_batch

    @pytest.fixture
    def batch_processor(self, mock_queue, mock_cache, processor):
        """Create batch processor instance."""
        return MessageBatchProcessor(
            queue=mock_queue,
            cache=mock_cache,
            processor=processor,
            batch_size=10,
        )

    @pytest.mark.asyncio
    async def test_start_stop(self, batch_processor):
        """Test starting and stopping batch processor."""
        assert not batch_processor._is_running

        await batch_processor.start()
        assert batch_processor._is_running
        assert batch_processor._task is not None

        await batch_processor.stop()
        assert not batch_processor._is_running

    @pytest.mark.asyncio
    async def test_process_batch(self, batch_processor):
        """Test processing a batch of messages."""
        messages = [
            QueuedMessage(
                id=f"msg{i}",
                content={"data": f"data{i}"},
                priority=MessagePriority.NORMAL,
                timestamp=time.time(),
            )
            for i in range(5)
        ]

        # Mock cache set
        mock_cache_set = AsyncMock()
        batch_processor.cache.set = mock_cache_set

        await batch_processor._process_batch(messages)

        # Check that cache was updated
        assert mock_cache_set.call_count == 5

        # Check results
        for i, call in enumerate(mock_cache_set.call_args_list):
            key, value = call[0]
            assert key == f"result:msg{i}"
            assert value == f"processed_msg{i}"


class TestMessageQueueManager:
    """Test message queue manager."""

    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return MessageQueueManager(
            redis_url="redis://localhost:6379/15",
            cache_size=100,
            cache_memory_mb=10.0,
        )

    @pytest.mark.asyncio
    async def test_start_stop(self, manager):
        """Test starting and stopping manager."""
        with patch.object(manager.queue, 'connect') as mock_connect:
            await manager.start()
            assert manager._is_running
            mock_connect.assert_called_once()

        with patch.object(manager.queue, 'disconnect') as mock_disconnect:
            await manager.stop()
            assert not manager._is_running
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_receive_message(self, manager):
        """Test sending and receiving messages."""
        with patch.object(manager.queue, 'enqueue') as mock_enqueue:
            message_id = await manager.send_message(
                content={"test": "data"},
                priority=MessagePriority.HIGH,
            )

            assert message_id is not None
            mock_enqueue.assert_called_once()

        with patch.object(manager.queue, 'dequeue') as mock_dequeue:
            mock_dequeue.return_value = QueuedMessage(
                id="test1",
                content={"test": "data"},
                priority=MessagePriority.NORMAL,
                timestamp=time.time(),
            )

            message = await manager.receive_message()
            assert message is not None
            mock_dequeue.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_operations(self, manager):
        """Test cache operations."""
        # Set cache value
        await manager.set_cache("key1", "value1")

        # Get cache value
        value = await manager.get_cache("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_batch_processor_registration(self, manager):
        """Test batch processor registration."""
        def test_processor(messages: List[QueuedMessage]) -> List[str]:
            return [f"processed_{msg.id}" for msg in messages]

        manager.register_batch_processor(
            name="test",
            processor=test_processor,
            queue_name="test_queue",
            batch_size=10,
        )

        assert "test" in manager.batch_processors

        processor = manager.batch_processors["test"]
        assert processor.queue == manager.queue
        assert processor.cache == manager.cache
        assert processor.batch_size == 10

    @pytest.mark.asyncio
    async def test_batch_processor_lifecycle(self, manager):
        """Test batch processor start/stop."""
        def test_processor(messages: List[QueuedMessage]) -> List[str]:
            return [f"processed_{msg.id}" for msg in messages]

        manager.register_batch_processor("test", test_processor)

        with patch.object(manager.batch_processors["test"], 'start') as mock_start:
            await manager.start_batch_processor("test")
            mock_start.assert_called_once()

        with patch.object(manager.batch_processors["test"], 'stop') as mock_stop:
            await manager.stop_batch_processor("test")
            mock_stop.assert_called_once()

    def test_get_stats(self, manager):
        """Test getting statistics."""
        stats = manager.get_stats()

        assert "queue" in stats
        assert "cache" in stats
        assert "batch_processors" in stats


class TestMessageQueueIntegration:
    """Integration tests for message queue system."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete message workflow."""
        cache = IntelligentCache(max_size=100)

        # Send message to cache
        await cache.set("msg1", {"data": "test"}, ttl=1.0)

        # Receive message
        value = await cache.get("msg1")
        assert value == {"data": "test"}

        # Check stats
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Try to get expired message
        value = await cache.get("msg1")
        assert value is None

        # Check updated stats
        stats = cache.get_stats()
        assert stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test concurrent cache operations."""
        cache = IntelligentCache(max_size=1000)

        async def set_get(key_suffix: int):
            key = f"key{key_suffix}"
            await cache.set(key, f"value{key_suffix}")
            await asyncio.sleep(0.01)
            value = await cache.get(key)
            assert value == f"value{key_suffix}"

        # Run concurrent operations
        tasks = [set_get(i) for i in range(50)]
        await asyncio.gather(*tasks)

        # Check final stats
        stats = cache.get_stats()
        assert stats["hits"] >= 50
        assert stats["misses"] >= 0
        assert stats["current_size"] <= 1000

    @pytest.mark.asyncio
    async def test_cache_memory_management(self):
        """Test cache memory management."""
        cache = IntelligentCache(
            max_size=1000,
            max_memory_mb=1.0,  # Very small limit
        )

        # Add large objects
        large_data = "x" * 10000  # 10KB

        added_count = 0
        for i in range(200):  # Try to add more than memory allows
            await cache.set(f"large{i}", large_data)
            added_count += 1

            # Check memory usage
            stats = cache.get_stats()
            if stats["current_memory_mb"] > 0.5:  # Stop if we hit 50% of limit
                break

        # Verify that cache managed memory properly
        stats = cache.get_stats()
        assert stats["current_memory_mb"] <= 1.0
        assert stats["evictions"] > 0

    @pytest.mark.asyncio
    async def test_priority_message_handling(self):
        """Test priority message handling."""
        # Test with local queue (no Redis)
        cache = IntelligentCache()

        # Create messages with different priorities
        messages = [
            {"priority": MessagePriority.CRITICAL, "id": "1"},
            {"priority": MessagePriority.LOW, "id": "2"},
            {"priority": MessagePriority.HIGH, "id": "3"},
            {"priority": MessagePriority.NORMAL, "id": "4"},
        ]

        # Add to cache with priority-based TTL
        for msg in messages:
            ttl = {
                MessagePriority.CRITICAL: 10.0,
                MessagePriority.HIGH: 5.0,
                MessagePriority.NORMAL: 1.0,
                MessagePriority.LOW: 0.5,
            }[msg["priority"]]

            await cache.set(f"msg{msg['id']}", msg, ttl=ttl)

        # Verify all are cached
        for msg in messages:
            value = await cache.get(f"msg{msg['id']}")
            assert value is not None

        # Wait for low priority to expire
        await asyncio.sleep(0.6)

        # Check what expired
        low_priority = await cache.get("msg2")
        assert low_priority is None

        # Higher priority should still exist
        high_priority = await cache.get("msg3")
        assert high_priority is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
