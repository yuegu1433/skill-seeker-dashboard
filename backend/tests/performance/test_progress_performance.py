"""Performance tests and monitoring for progress tracking system.

This module provides comprehensive performance testing including:
- Benchmark tests for throughput and latency
- Stress tests for concurrent connections
- Memory usage monitoring
- Real-time performance monitoring and alerting
"""

import asyncio
import gc
import psutil
import pytest
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from unittest.mock import MagicMock, patch
import statistics

from backend.app.progress.websocket_manager import WebSocketManager, ConnectionPool
from backend.app.progress.connection_pool import connection_pool_manager, ResourceMonitor
from backend.app.progress.message_queue import message_queue_manager, IntelligentCache, QueuedMessage


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    active_connections: int
    messages_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    throughput_mbps: float = 0.0


@dataclass
class BenchmarkResult:
    """Benchmark test result."""
    test_name: str
    duration_seconds: float
    operations: int
    operations_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    error_rate: float
    throughput_mbps: float
    memory_usage_mb: float
    cpu_usage_percent: float


class PerformanceMonitor:
    """Real-time performance monitoring."""

    def __init__(self, window_size: int = 100):
        """Initialize performance monitor.

        Args:
            window_size: Number of metrics to keep in window
        """
        self.window_size = window_size
        self.metrics_history: deque = deque(maxlen=window_size)
        self.alerts: List[Dict[str, Any]] = []
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_mb": 1024.0,
            "latency_ms": 100.0,
            "error_rate": 0.01,  # 1%
            "connections": 1000,
        }

    def set_thresholds(self, **thresholds):
        """Set alert thresholds.

        Args:
            **thresholds: Threshold values
        """
        self.thresholds.update(thresholds)

    def record_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics.

        Args:
            metrics: Performance metrics to record
        """
        self.metrics_history.append(metrics)

        # Check thresholds
        self._check_thresholds(metrics)

    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check metrics against thresholds.

        Args:
            metrics: Performance metrics to check
        """
        alerts = []

        if metrics.cpu_percent > self.thresholds.get("cpu_percent", 80.0):
            alerts.append({
                "type": "cpu_high",
                "message": f"CPU usage ({metrics.cpu_percent:.1f}%) exceeds threshold",
                "value": metrics.cpu_percent,
                "threshold": self.thresholds["cpu_percent"],
            })

        if metrics.memory_mb > self.thresholds.get("memory_mb", 1024.0):
            alerts.append({
                "type": "memory_high",
                "message": f"Memory usage ({metrics.memory_mb:.1f}MB) exceeds threshold",
                "value": metrics.memory_mb,
                "threshold": self.thresholds["memory_mb"],
            })

        if metrics.avg_latency_ms > self.thresholds.get("latency_ms", 100.0):
            alerts.append({
                "type": "latency_high",
                "message": f"Average latency ({metrics.avg_latency_ms:.1f}ms) exceeds threshold",
                "value": metrics.avg_latency_ms,
                "threshold": self.thresholds["latency_ms"],
            })

        if metrics.error_rate > self.thresholds.get("error_rate", 0.01):
            alerts.append({
                "type": "error_rate_high",
                "message": f"Error rate ({metrics.error_rate:.1%}) exceeds threshold",
                "value": metrics.error_rate,
                "threshold": self.thresholds["error_rate"],
            })

        if metrics.active_connections > self.thresholds.get("connections", 1000):
            alerts.append({
                "type": "connections_high",
                "message": f"Active connections ({metrics.active_connections}) exceeds threshold",
                "value": metrics.active_connections,
                "threshold": self.thresholds["connections"],
            })

        if alerts:
            self.alerts.extend(alerts)
            for alert in alerts:
                print(f"ALERT: {alert['message']}")

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get latest metrics.

        Returns:
            Latest metrics or None
        """
        return self.metrics_history[-1] if self.metrics_history else None

    def get_average_metrics(self, window: Optional[int] = None) -> Optional[PerformanceMetrics]:
        """Get average metrics over window.

        Args:
            window: Number of samples to average

        Returns:
            Average metrics or None
        """
        if not self.metrics_history:
            return None

        window = window or len(self.metrics_history)
        recent = list(self.metrics_history)[-window:]

        if not recent:
            return None

        return PerformanceMetrics(
            timestamp=statistics.mean(m.timestamp for m in recent),
            cpu_percent=statistics.mean(m.cpu_percent for m in recent),
            memory_mb=statistics.mean(m.memory_mb for m in recent),
            active_connections=int(statistics.mean(m.active_connections for m in recent)),
            messages_per_second=statistics.mean(m.messages_per_second for m in recent),
            avg_latency_ms=statistics.mean(m.avg_latency_ms for m in recent),
            p95_latency_ms=statistics.mean(m.p95_latency_ms for m in recent),
            p99_latency_ms=statistics.mean(m.p99_latency_ms for m in recent),
            error_rate=statistics.mean(m.error_rate for m in recent),
            throughput_mbps=statistics.mean(m.throughput_mbps for m in recent),
        )

    def get_percentile_latencies(self, percentile: float) -> float:
        """Get percentile latency.

        Args:
            percentile: Percentile (0-100)

        Returns:
            Latency value
        """
        if not self.metrics_history:
            return 0.0

        latencies = [m.avg_latency_ms for m in self.metrics_history]
        return statistics.quantiles(latencies, n=100)[int(percentile) - 1]

    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()


class WebSocketPerformanceTest:
    """WebSocket performance testing."""

    def __init__(self, monitor: PerformanceMonitor):
        """Initialize WebSocket performance test.

        Args:
            monitor: Performance monitor
        """
        self.monitor = monitor
        self.websocket_manager = WebSocketManager(max_connections=1000)

    async def benchmark_concurrent_connections(
        self,
        num_connections: int = 100,
        duration_seconds: float = 10.0,
    ) -> BenchmarkResult:
        """Benchmark concurrent WebSocket connections.

        Args:
            num_connections: Number of concurrent connections
            duration_seconds: Test duration

        Returns:
            Benchmark result
        """
        print(f"\n=== Benchmarking {num_connections} concurrent connections ===")

        # Start WebSocket manager
        await self.websocket_manager.start()

        start_time = time.time()
        end_time = start_time + duration_seconds
        latencies = []
        messages_sent = 0
        messages_failed = 0
        connection_count = 0

        # Create mock WebSocket connections
        connections = []
        for i in range(num_connections):
            try:
                mock_ws = MagicMock()
                mock_ws.application_state.CONNECTED = True
                mock_ws.send_text = AsyncMock()

                connection_id = await self.websocket_manager.connect(
                    websocket=mock_ws,
                    task_id=f"task_{i}",
                    user_id=f"user_{i % 10}",
                )

                if connection_id:
                    connections.append((connection_id, mock_ws))
                    connection_count += 1

            except Exception as e:
                print(f"Failed to create connection {i}: {e}")
                messages_failed += 1

        print(f"Created {connection_count} connections")

        # Send messages during test
        tasks = []
        while time.time() < end_time:
            for connection_id, mock_ws in connections:
                send_start = time.time()

                try:
                    await self.websocket_manager.send_message(
                        connection_id,
                        {"type": "test", "data": "message"}
                    )
                    messages_sent += 1

                    latency = (time.time() - send_start) * 1000
                    latencies.append(latency)

                except Exception as e:
                    messages_failed += 1
                    print(f"Failed to send message: {e}")

                await asyncio.sleep(0.01)  # Small delay between sends

        # Cleanup
        for connection_id, _ in connections:
            await self.websocket_manager.disconnect(connection_id)

        await self.websocket_manager.stop()

        # Calculate metrics
        actual_duration = time.time() - start_time
        total_messages = messages_sent + messages_failed
        operations_per_second = messages_sent / actual_duration
        error_rate = messages_failed / total_messages if total_messages > 0 else 0

        # Calculate latency percentiles
        if latencies:
            latencies.sort()
            p50 = latencies[int(len(latencies) * 0.5)]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
        else:
            p50 = p95 = p99 = avg_latency = min_latency = max_latency = 0

        # Get system metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return BenchmarkResult(
            test_name=f"Concurrent Connections ({num_connections})",
            duration_seconds=actual_duration,
            operations=messages_sent,
            operations_per_second=operations_per_second,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            error_rate=error_rate,
            throughput_mbps=0.0,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
        )


class CachePerformanceTest:
    """Cache performance testing."""

    def __init__(self, monitor: PerformanceMonitor):
        """Initialize cache performance test.

        Args:
            monitor: Performance monitor
        """
        self.monitor = monitor

    async def benchmark_cache_operations(
        self,
        num_operations: int = 10000,
        key_size: int = 100,
    ) -> BenchmarkResult:
        """Benchmark cache operations.

        Args:
            num_operations: Number of operations
            key_size: Size of test data

        Returns:
            Benchmark result
        """
        print(f"\n=== Benchmarking {num_operations} cache operations ===")

        cache = IntelligentCache(max_size=10000)
        start_time = time.time()
        latencies = []
        hits = 0
        misses = 0

        # Generate test data
        test_data = {
            f"key_{i}": f"value_{i}_{'x' * key_size}"
            for i in range(num_operations)
        }

        # Benchmark SET operations
        set_latencies = []
        for key, value in test_data.items():
            op_start = time.time()
            await cache.set(key, value)
            latency = (time.time() - op_start) * 1000
            set_latencies.append(latency)

        # Benchmark GET operations (50% hit rate)
        get_latencies = []
        for i in range(num_operations):
            key = f"key_{i}" if i % 2 == 0 else f"nonexistent_{i}"
            op_start = time.time()
            value = await cache.get(key)
            latency = (time.time() - op_start) * 1000
            get_latencies.append(latency)

            if value:
                hits += 1
            else:
                misses += 1

        duration = time.time() - start_time
        all_latencies = set_latencies + get_latencies

        # Calculate percentiles
        all_latencies.sort()
        p50 = all_latencies[int(len(all_latencies) * 0.5)]
        p95 = all_latencies[int(len(all_latencies) * 0.95)]
        p99 = all_latencies[int(len(all_latencies) * 0.99)]
        avg_latency = statistics.mean(all_latencies)
        min_latency = min(all_latencies)
        max_latency = max(all_latencies)

        # Get stats
        stats = cache.get_stats()
        error_rate = 0.0  # Cache operations don't fail, they just miss

        return BenchmarkResult(
            test_name=f"Cache Operations ({num_operations})",
            duration_seconds=duration,
            operations=num_operations * 2,  # SET + GET
            operations_per_second=(num_operations * 2) / duration,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            error_rate=error_rate,
            throughput_mbps=0.0,
            memory_usage_mb=stats["current_memory_mb"],
            cpu_usage_percent=psutil.cpu_percent(interval=0.1),
        )


class StressTest:
    """System stress testing."""

    def __init__(self, monitor: PerformanceMonitor):
        """Initialize stress test.

        Args:
            monitor: Performance monitor
        """
        self.monitor = monitor

    async def run_stress_test(
        self,
        duration_seconds: float = 60.0,
        connection_count: int = 500,
        message_rate: float = 10.0,
    ) -> List[PerformanceMetrics]:
        """Run stress test.

        Args:
            duration_seconds: Test duration
            connection_count: Number of connections
            message_rate: Messages per second per connection

        Returns:
            List of performance metrics
        """
        print(f"\n=== Running stress test ({duration_seconds}s) ===")
        print(f"Connections: {connection_count}, Rate: {message_rate} msg/s")

        ws_test = WebSocketPerformanceTest(self.monitor)
        cache_test = CachePerformanceTest(self.monitor)

        # Start WebSocket manager
        await ws_test.websocket_manager.start()

        start_time = time.time()
        metrics_history = []

        # Create connections
        connections = []
        for i in range(connection_count):
            try:
                mock_ws = MagicMock()
                mock_ws.application_state.CONNECTED = True
                mock_ws.send_text = AsyncMock()

                connection_id = await ws_test.websocket_manager.connect(
                    websocket=mock_ws,
                    task_id=f"stress_task_{i}",
                )

                if connection_id:
                    connections.append((connection_id, mock_ws))

            except Exception:
                pass

        print(f"Created {len(connections)} connections")

        # Run test
        task = asyncio.create_task(self._stress_test_loop(
            connections,
            duration_seconds,
            message_rate,
            metrics_history,
        ))

        await task

        # Cleanup
        for connection_id, _ in connections:
            await ws_test.websocket_manager.disconnect(connection_id)

        await ws_test.websocket_manager.stop()

        print(f"\nStress test completed. Collected {len(metrics_history)} metrics.")
        return metrics_history

    async def _stress_test_loop(
        self,
        connections: List,
        duration_seconds: float,
        message_rate: float,
        metrics_history: List[PerformanceMetrics],
    ):
        """Stress test main loop.

        Args:
            connections: Active connections
            duration_seconds: Test duration
            message_rate: Message rate
            metrics_history: Metrics collection list
        """
        start_time = time.time()
        end_time = start_time + duration_seconds
        message_count = 0
        error_count = 0
        latencies = []

        while time.time() < end_time:
            loop_start = time.time()

            # Send messages
            for connection_id, mock_ws in connections:
                try:
                    msg_start = time.time()
                    await ws_test.websocket_manager.send_message(
                        connection_id,
                        {"type": "stress", "data": f"msg_{message_count}"}
                    )
                    latency = (time.time() - msg_start) * 1000
                    latencies.append(latency)
                    message_count += 1

                except Exception:
                    error_count += 1

            # Collect metrics every second
            await asyncio.sleep(1.0)

            # Calculate metrics
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            current_time = time.time()
            elapsed = current_time - start_time
            messages_per_second = message_count / elapsed if elapsed > 0 else 0

            if latencies:
                avg_latency = statistics.mean(latencies[-100:])  # Last 100 messages
                p95_latency = statistics.quantiles(latencies[-100:], n=100)[94]
                p99_latency = statistics.quantiles(latencies[-100:], n=100)[98]
            else:
                avg_latency = p95_latency = p99_latency = 0

            error_rate = error_count / message_count if message_count > 0 else 0

            metrics = PerformanceMetrics(
                timestamp=current_time,
                cpu_percent=psutil.cpu_percent(interval=0.1),
                memory_mb=memory_mb,
                active_connections=len(connections),
                messages_per_second=messages_per_second,
                avg_latency_ms=avg_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                error_rate=error_rate,
            )

            self.monitor.record_metrics(metrics)
            metrics_history.append(metrics)

            # Print progress
            progress = (elapsed / duration_seconds) * 100
            print(f"\rProgress: {progress:.1f}% - "
                  f"Messages: {message_count} - "
                  f"Rate: {messages_per_second:.1f}/s - "
                  f"Latency: {avg_latency:.1f}ms", end="", flush=True)


class TestWebSocketPerformance:
    """Test WebSocket performance."""

    @pytest.fixture
    def monitor(self):
        """Create performance monitor."""
        return PerformanceMonitor()

    @pytest.fixture
    def ws_test(self, monitor):
        """Create WebSocket performance test."""
        return WebSocketPerformanceTest(monitor)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_connections_small(self, ws_test):
        """Test small number of concurrent connections."""
        result = await ws_test.benchmark_concurrent_connections(
            num_connections=50,
            duration_seconds=5.0,
        )

        print(f"\nResult: {result.operations_per_second:.2f} ops/sec")
        assert result.operations_per_second > 10
        assert result.error_rate < 0.1

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_connections_medium(self, ws_test):
        """Test medium number of concurrent connections."""
        result = await ws_test.benchmark_concurrent_connections(
            num_connections=200,
            duration_seconds=10.0,
        )

        print(f"\nResult: {result.operations_per_second:.2f} ops/sec")
        assert result.operations_per_second > 5
        assert result.error_rate < 0.05

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_connections_large(self, ws_test):
        """Test large number of concurrent connections."""
        result = await ws_test.benchmark_concurrent_connections(
            num_connections=500,
            duration_seconds=15.0,
        )

        print(f"\nResult: {result.operations_per_second:.2f} ops/sec")
        assert result.operations_per_second > 2
        assert result.error_rate < 0.01


class TestCachePerformance:
    """Test cache performance."""

    @pytest.fixture
    def monitor(self):
        """Create performance monitor."""
        return PerformanceMonitor()

    @pytest.fixture
    def cache_test(self, monitor):
        """Create cache performance test."""
        return CachePerformanceTest(monitor)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_operations_small(self, cache_test):
        """Test small number of cache operations."""
        result = await cache_test.benchmark_cache_operations(
            num_operations=1000,
            key_size=100,
        )

        print(f"\nResult: {result.operations_per_second:.2f} ops/sec")
        assert result.operations_per_second > 1000
        assert result.avg_latency_ms < 1.0

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_operations_medium(self, cache_test):
        """Test medium number of cache operations."""
        result = await cache_test.benchmark_cache_operations(
            num_operations=5000,
            key_size=500,
        )

        print(f"\nResult: {result.operations_per_second:.2f} ops/sec")
        assert result.operations_per_second > 500
        assert result.avg_latency_ms < 2.0

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_cache_operations_large(self, cache_test):
        """Test large number of cache operations."""
        result = await cache_test.benchmark_cache_operations(
            num_operations=10000,
            key_size=1000,
        )

        print(f"\nResult: {result.operations_per_second:.2f} ops/sec")
        assert result.operations_per_second > 200
        assert result.avg_latency_ms < 5.0


class TestStressTest:
    """Test system under stress."""

    @pytest.fixture
    def monitor(self):
        """Create performance monitor."""
        return PerformanceMonitor()

    @pytest.fixture
    def stress_test(self, monitor):
        """Create stress test."""
        return StressTest(monitor)

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_stress_short(self, stress_test):
        """Test short stress scenario."""
        metrics = await stress_test.run_stress_test(
            duration_seconds=30.0,
            connection_count=100,
            message_rate=5.0,
        )

        # Check system remained stable
        assert len(metrics) > 0

        # Check error rate stayed low
        avg_error_rate = statistics.mean(m.error_rate for m in metrics)
        assert avg_error_rate < 0.05

        # Check memory usage stayed reasonable
        avg_memory = statistics.mean(m.memory_mb for m in metrics)
        assert avg_memory < 512.0  # Less than 512MB

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_stress_medium(self, stress_test):
        """Test medium stress scenario."""
        metrics = await stress_test.run_stress_test(
            duration_seconds=60.0,
            connection_count=300,
            message_rate=10.0,
        )

        # Check system remained stable
        assert len(metrics) > 0

        # Check error rate stayed low
        avg_error_rate = statistics.mean(m.error_rate for m in metrics)
        assert avg_error_rate < 0.1

        # Check average latency stayed reasonable
        avg_latency = statistics.mean(m.avg_latency_ms for m in metrics)
        assert avg_latency < 100.0


class TestPerformanceMonitoring:
    """Test performance monitoring."""

    @pytest.fixture
    def monitor(self):
        """Create performance monitor."""
        return PerformanceMonitor()

    def test_metric_recording(self, monitor):
        """Test recording metrics."""
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=50.0,
            memory_mb=512.0,
            active_connections=100,
            messages_per_second=1000.0,
            avg_latency_ms=10.0,
            p95_latency_ms=20.0,
            p99_latency_ms=30.0,
            error_rate=0.01,
        )

        monitor.record_metrics(metrics)

        assert len(monitor.metrics_history) == 1
        assert monitor.get_current_metrics() == metrics

    def test_threshold_alerts(self, monitor):
        """Test threshold alerts."""
        monitor.set_thresholds(cpu_percent=50.0)

        # Create metrics that exceed threshold
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=80.0,  # Exceeds 50% threshold
            memory_mb=512.0,
            active_connections=100,
            messages_per_second=1000.0,
            avg_latency_ms=10.0,
            p95_latency_ms=20.0,
            p99_latency_ms=30.0,
            error_rate=0.01,
        )

        monitor.record_metrics(metrics)

        assert len(monitor.alerts) > 0
        assert any(alert["type"] == "cpu_high" for alert in monitor.alerts)

    def test_average_metrics(self, monitor):
        """Test calculating average metrics."""
        for i in range(5):
            metrics = PerformanceMetrics(
                timestamp=time.time() + i,
                cpu_percent=10.0 * (i + 1),
                memory_mb=100.0 * (i + 1),
                active_connections=i,
                messages_per_second=100.0 * (i + 1),
                avg_latency_ms=10.0 * (i + 1),
                p95_latency_ms=20.0 * (i + 1),
                p99_latency_ms=30.0 * (i + 1),
                error_rate=0.01 * (i + 1),
            )
            monitor.record_metrics(metrics)

        avg = monitor.get_average_metrics()
        assert avg is not None
        assert avg.cpu_percent == 30.0  # Average of 10,20,30,40,50
        assert avg.memory_mb == 300.0  # Average of 100,200,300,400,500


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])
