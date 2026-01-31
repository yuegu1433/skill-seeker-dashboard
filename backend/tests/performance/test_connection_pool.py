"""Tests for connection pool and resource management.

This module tests the advanced connection pooling, resource monitoring,
and auto-scaling features.
"""

import asyncio
import pytest
import time
from unittest.mock import MagicMock, patch, AsyncMock
from typing import List

from backend.app.progress.connection_pool (
    ConnectionPoolManager,
    ConnectionPoolConfig,
    ResourceMonitor,
    ResourceMetrics,
    ResourceType,
    PoolStatus,
    connection_pool_manager,
    reuse_strategy,
)


class TestResourceMonitor:
    """Test resource monitoring functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ConnectionPoolConfig(
            max_connections=100,
            memory_limit_mb=512.0,
            cpu_threshold=70.0,
        )

    @pytest.fixture
    def monitor(self, config):
        """Create resource monitor instance."""
        return ResourceMonitor(config)

    def test_get_current_metrics(self, monitor):
        """Test getting current resource metrics."""
        metrics = monitor.get_current_metrics()

        assert isinstance(metrics, ResourceMetrics)
        assert metrics.cpu_percent >= 0
        assert metrics.memory_mb >= 0
        assert metrics.memory_percent >= 0
        assert metrics.active_connections >= 0
        assert metrics.queued_messages >= 0

    def test_check_thresholds(self, monitor):
        """Test threshold checking."""
        # Test normal metrics
        normal_metrics = ResourceMetrics(
            cpu_percent=50.0,
            memory_mb=300.0,
            memory_percent=60.0,
            active_connections=50,
            queued_messages=500,
        )
        is_critical, warnings = monitor.check_thresholds(normal_metrics)
        assert not is_critical
        assert len(warnings) == 0

        # Test exceeded thresholds
        high_metrics = ResourceMetrics(
            cpu_percent=85.0,
            memory_mb=600.0,
            memory_percent=90.0,
            active_connections=90,
            queued_messages=950,
        )
        is_critical, warnings = monitor.check_thresholds(high_metrics)
        assert is_critical
        assert len(warnings) > 0
        assert any("Memory usage" in w for w in warnings)
        assert any("CPU usage" in w for w in warnings)

    def test_add_callback(self, monitor):
        """Test adding resource alert callbacks."""
        callback_called = []

        def test_callback(metrics):
            callback_called.append(metrics)

        monitor.add_callback(test_callback)

        # Trigger callback by getting metrics
        metrics = monitor.get_current_metrics()
        assert len(callback_called) == 1
        assert callback_called[0] == metrics

    @pytest.mark.asyncio
    async def test_metrics_history(self, monitor):
        """Test metrics history tracking."""
        # Get multiple metrics
        for _ in range(5):
            monitor.get_current_metrics()
            await asyncio.sleep(0.01)

        # Check history
        assert len(monitor.metrics_history) == 5

        # Get average metrics
        avg_metrics = monitor.get_average_metrics(3)
        assert isinstance(avg_metrics, ResourceMetrics)


class TestConnectionPoolManager:
    """Test connection pool manager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ConnectionPoolConfig(
            max_connections=100,
            max_connections_per_user=10,
            max_connections_per_task=5,
            min_idle_connections=10,
            max_idle_connections=50,
        )

    @pytest.fixture
    def pool_manager(self, config):
        """Create pool manager instance."""
        return ConnectionPoolManager(config)

    @pytest.fixture
    def mock_websocket_manager(self):
        """Create mock WebSocket manager."""
        mock_manager = MagicMock()
        mock_pool = MagicMock()

        # Setup connection pool mock
        mock_pool.connections = {}
        mock_pool.get_connection_count.return_value = 0
        mock_pool.get_user_connection_count.return_value = 0
        mock_pool.get_task_connection_count.return_value = 0

        mock_manager.connection_pool = mock_pool

        return mock_manager

    @pytest.mark.asyncio
    async def test_start_stop(self, pool_manager):
        """Test starting and stopping pool manager."""
        assert not pool_manager._is_running

        await pool_manager.start()
        assert pool_manager._is_running
        assert pool_manager._monitor_task is not None
        assert pool_manager._cleanup_task is not None

        await pool_manager.stop()
        assert not pool_manager._is_running

    @pytest.mark.asyncio
    async def test_acquire_connection(self, pool_manager, mock_websocket_manager):
        """Test acquiring connection slot."""
        with patch('backend.app.progress.connection_pool.websocket_manager', mock_websocket_manager):
            # Setup mock connection
            mock_connection = MagicMock()
            mock_connection.id = "test_connection"
            mock_websocket_manager.connection_pool.connections["test_connection"] = mock_connection

            # Test successful acquisition
            result = await pool_manager.acquire_connection(
                connection_id="test_connection",
                user_id="test_user",
                task_id="test_task",
            )
            assert result is True

            # Test user limit exceeded
            mock_websocket_manager.connection_pool.get_user_connection_count.return_value = 10
            result = await pool_manager.acquire_connection(
                connection_id="test_connection_2",
                user_id="test_user",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_release_connection(self, pool_manager):
        """Test releasing connection slot."""
        initial_created = pool_manager.stats["total_connections_created"]
        initial_closed = pool_manager.stats["total_connections_closed"]

        await pool_manager.release_connection("test_connection", lifetime=10.5)

        assert pool_manager.stats["total_connections_created"] == initial_created + 1
        assert pool_manager.stats["total_connections_closed"] == initial_closed + 1
        assert pool_manager.stats["avg_connection_lifetime"] == 10.5

    @pytest.mark.asyncio
    async def test_optimize_connections(self, pool_manager, mock_websocket_manager):
        """Test connection optimization."""
        with patch('backend.app.progress.connection_pool.websocket_manager', mock_websocket_manager):
            # Test normal optimization
            await pool_manager.optimize_connections()

            # Test emergency cleanup
            with patch.object(pool_manager, '_trigger_emergency_cleanup') as mock_emergency:
                # Simulate critical metrics
                with patch.object(pool_manager.resource_monitor, 'get_current_metrics') as mock_metrics:
                    mock_metrics.return_value = ResourceMetrics(
                        cpu_percent=90.0,
                        memory_mb=2000.0,
                        memory_percent=95.0,
                    )
                    with patch.object(pool_manager.resource_monitor, 'check_thresholds') as mock_check:
                        mock_check.return_value = (True, ["High memory usage"])

                        await pool_manager.optimize_connections()
                        assert mock_emergency.called

    @pytest.mark.asyncio
    async def test_scale_down(self, pool_manager, mock_websocket_manager):
        """Test scaling down connections."""
        with patch('backend.app.progress.connection_pool.websocket_manager', mock_websocket_manager):
            # Setup mock connections
            for i in range(5):
                mock_connection = MagicMock()
                mock_connection.get_idle_time.return_value = 120.0  # Idle for 2 minutes
                mock_websocket_manager.connection_pool.connections[f"conn_{i}"] = mock_connection

            mock_websocket_manager.connection_pool.get_connection_count.return_value = 5

            # Trigger scale down
            await pool_manager._scale_down_connections(ResourceMetrics(active_connections=5))

            # Verify disconnections were attempted
            assert mock_websocket_manager.disconnect.called

    @pytest.mark.asyncio
    async def test_monitor_loop(self, pool_manager):
        """Test background monitoring loop."""
        await pool_manager.start()

        # Let it run for a short time
        await asyncio.sleep(0.1)

        # Check status is set
        assert pool_manager.status in [PoolStatus.HEALTHY, PoolStatus.DEGRADED, PoolStatus.CRITICAL, PoolStatus.OVERLOADED]

        await pool_manager.stop()

    @pytest.mark.asyncio
    async def test_cleanup_loop(self, pool_manager):
        """Test background cleanup loop."""
        await pool_manager.start()

        # Let it run for a short time
        await asyncio.sleep(0.1)

        await pool_manager.stop()

    @pytest.mark.asyncio
    async def test_force_cleanup(self, pool_manager, mock_websocket_manager):
        """Test forced cleanup."""
        with patch('backend.app.progress.connection_pool.websocket_manager', mock_websocket_manager):
            # Setup mock dead connection
            mock_connection = MagicMock()
            mock_connection.is_alive = False
            mock_websocket_manager.connection_pool.connections["dead_conn"] = mock_connection

            await pool_manager.force_cleanup()

            # Verify disconnect was called
            assert mock_websocket_manager.disconnect.called

    def test_get_pool_status(self, pool_manager):
        """Test getting pool status."""
        status = asyncio.run(pool_manager.get_pool_status())

        assert "status" in status
        assert "is_critical" in status
        assert "warnings" in status
        assert "metrics" in status
        assert "stats" in status
        assert "config" in status
        assert status["status"] in [s.value for s in PoolStatus]

    def test_get_connection_reuse_stats(self, pool_manager):
        """Test getting connection reuse statistics."""
        # Test with no data
        stats = pool_manager.get_connection_reuse_stats()
        assert stats["total_tracked"] == 0
        assert stats["avg_reuse_count"] == 0

        # Add some data
        pool_manager.connection_reuse_tracker["conn1"] = 5
        pool_manager.connection_reuse_tracker["conn2"] = 10
        pool_manager.connection_reuse_tracker["conn3"] = 7

        stats = pool_manager.get_connection_reuse_stats()
        assert stats["total_tracked"] == 3
        assert stats["avg_reuse_count"] == pytest.approx(7.33, rel=1e-2)
        assert stats["max_reuse_count"] == 10
        assert stats["min_reuse_count"] == 5


class TestConnectionReuseStrategy:
    """Test connection reuse strategy."""

    @pytest.fixture
    def strategy(self):
        """Create reuse strategy instance."""
        return reuse_strategy

    @pytest.mark.asyncio
    async def test_analyze_reuse_pattern(self, strategy):
        """Test analyzing reuse patterns."""
        await strategy.analyze_reuse_pattern(
            connection_id="conn1",
            user_id="user1",
            task_id="task1",
        )

        pattern_key = "user1:task1"
        assert pattern_key in strategy.reuse_patterns
        assert len(strategy.reuse_patterns[pattern_key]) == 1

    @pytest.mark.asyncio
    async def test_predict_reuse_opportunity(self, strategy):
        """Test predicting reuse opportunities."""
        # Test with no patterns
        score = await strategy.predict_reuse_opportunity("user1", "task1")
        assert score == 0.0

        # Add some patterns
        current_time = time.time()
        for _ in range(5):
            strategy.reuse_patterns["user1:task1"].append(current_time)

        score = await strategy.predict_reuse_opportunity("user1", "task1")
        assert score > 0.0
        assert score <= 1.0

    @pytest.mark.asyncio
    async def test_get_preferred_connection(self, strategy):
        """Test getting preferred connection."""
        # Setup reuse tracker
        strategy.manager.connection_reuse_tracker["conn1"] = 5
        strategy.manager.connection_reuse_tracker["conn2"] = 10
        strategy.manager.connection_reuse_tracker["conn3"] = 7

        # Test with available connections
        preferred = await strategy.get_preferred_connection(
            user_id="user1",
            task_id="task1",
            available_connections=["conn1", "conn2", "conn3"],
        )
        assert preferred == "conn2"  # Highest reuse count

        # Test with no connections
        preferred = await strategy.get_preferred_connection(
            user_id="user1",
            task_id="task1",
            available_connections=[],
        )
        assert preferred is None


class TestConnectionPoolIntegration:
    """Integration tests for connection pool."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full connection pool workflow."""
        config = ConnectionPoolConfig(
            max_connections=10,
            min_idle_connections=2,
            enable_auto_scaling=True,
        )

        manager = ConnectionPoolManager(config)

        with patch('backend.app.progress.connection_pool.websocket_manager') as mock_ws:
            await manager.start()

            # Simulate connection acquisition
            await manager.acquire_connection(
                connection_id="conn1",
                user_id="user1",
                task_id="task1",
            )

            # Simulate connection release
            await manager.release_connection("conn1", lifetime=5.0)

            # Get status
            status = await manager.get_pool_status()
            assert status["status"] in [s.value for s in PoolStatus]

            # Force cleanup
            await manager.force_cleanup()

            await manager.stop()

    @pytest.mark.asyncio
    async def test_resource_alerts(self):
        """Test resource alert handling."""
        config = ConnectionPoolConfig(
            memory_limit_mb=100.0,
            cpu_threshold=50.0,
        )

        manager = ConnectionPoolManager(config)
        alert_received = []

        def alert_callback(metrics):
            alert_received.append(metrics)

        manager.resource_monitor.add_callback(alert_callback)

        with patch('backend.app.progress.connection_pool.websocket_manager') as mock_ws:
            await manager.start()

            # Trigger alert by setting high metrics
            with patch.object(manager.resource_monitor, 'get_current_metrics') as mock_metrics:
                mock_metrics.return_value = ResourceMetrics(
                    cpu_percent=60.0,
                    memory_mb=150.0,
                )

                # Let monitor run
                await asyncio.sleep(0.1)

            await manager.stop()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent connection operations."""
        config = ConnectionPoolConfig(max_connections=100)
        manager = ConnectionPoolManager(config)

        async def acquire_release(conn_id):
            await manager.acquire_connection(conn_id, user_id="user1")
            await asyncio.sleep(0.01)
            await manager.release_connection(conn_id, lifetime=1.0)

        with patch('backend.app.progress.connection_pool.websocket_manager') as mock_ws:
            await manager.start()

            # Run multiple concurrent operations
            tasks = [acquire_release(f"conn{i}") for i in range(20)]
            await asyncio.gather(*tasks)

            # Check statistics
            stats = manager.get_pool_status()["stats"]
            assert stats["total_connections_created"] == 20
            assert stats["total_connections_closed"] == 20

            await manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
