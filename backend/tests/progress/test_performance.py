"""Performance tests for real-time progress tracking.

This module contains comprehensive performance tests including:
- API performance tests
- WebSocket performance tests
- Database performance tests
- Cache performance tests
- System resource tests
"""

import pytest
import asyncio
import time
import statistics
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any
import psutil

from app.progress.performance_benchmark import (
    BenchmarkSuite,
    BenchmarkConfig,
    APIBenchmark,
    WebSocketBenchmark,
    DatabaseBenchmark,
    CacheBenchmark,
    BenchmarkType,
    BenchmarkReporter,
)
from app.progress.performance_monitor import (
    PerformanceDashboard,
    MetricType,
    AlertSeverity,
)
from app.progress.redis_message_queue import (
    RedisMessageQueue,
    QueueConfig,
    MessagePriority,
    MessageStatus,
)
from app.progress.multi_level_cache import (
    MultiLevelCache,
    CacheConfig,
    CacheLevel,
    EvictionPolicy,
)
from app.progress.database_pool import (
    DatabaseConnectionPool,
    DatabaseConfig,
    DatabaseType,
)


# Test configurations
@pytest.fixture
def benchmark_config():
    """Create benchmark configuration."""
    return BenchmarkConfig(
        test_name="test_benchmark",
        duration_seconds=5,
        concurrent_users=10,
        warmup_seconds=2,
        cooldown_seconds=2,
        target_rps=100,
        max_errors=10,
        collect_detailed_metrics=True,
    )


@pytest.fixture
async def performance_dashboard():
    """Create performance dashboard."""
    dashboard = PerformanceDashboard()
    await dashboard.start(system_interval=1.0, alert_interval=2.0)
    yield dashboard
    await dashboard.stop()


# ============================================================================
# Benchmark Tests
# ============================================================================

class TestBenchmarks:
    """Test performance benchmarks."""

    @pytest.mark.asyncio
    async def test_api_benchmark(self, benchmark_config):
        """Test API performance benchmark."""
        benchmark = APIBenchmark(benchmark_config)
        result = await benchmark.run()

        # Verify result
        assert result.benchmark_type == BenchmarkType.API_LATENCY
        assert result.duration_seconds > 0
        assert result.operations_count > 0
        assert result.operations_per_second > 0
        assert result.latency_ms > 0
        assert 0 <= result.success_rate <= 1
        assert result.error_count >= 0
        assert result.memory_usage_mb > 0

    @pytest.mark.asyncio
    async def test_websocket_benchmark(self, benchmark_config):
        """Test WebSocket performance benchmark."""
        benchmark = WebSocketBenchmark(benchmark_config)
        result = await benchmark.run()

        # Verify result
        assert result.benchmark_type == BenchmarkType.WEBSOCKET_CONNECTIONS
        assert result.duration_seconds > 0
        assert result.operations_count > 0
        assert result.operations_per_second > 0
        assert result.latency_ms > 0
        assert 0 <= result.success_rate <= 1

    @pytest.mark.asyncio
    async def test_database_benchmark(self, benchmark_config):
        """Test database performance benchmark."""
        benchmark = DatabaseBenchmark(benchmark_config)
        result = await benchmark.run()

        # Verify result
        assert result.benchmark_type == BenchmarkType.DATABASE_QUERIES
        assert result.duration_seconds > 0
        assert result.operations_count > 0
        assert result.operations_per_second > 0
        assert result.latency_ms > 0
        assert 0 <= result.success_rate <= 1

    @pytest.mark.asyncio
    async def test_cache_benchmark(self, benchmark_config):
        """Test cache performance benchmark."""
        benchmark = CacheBenchmark(benchmark_config)
        result = await benchmark.run()

        # Verify result
        assert result.benchmark_type == BenchmarkType.CACHE_PERFORMANCE
        assert result.duration_seconds > 0
        assert result.operations_count > 0
        assert result.operations_per_second > 0
        assert result.latency_ms > 0
        assert 0 <= result.success_rate <= 1


# ============================================================================
# Benchmark Suite Tests
# ============================================================================

class TestBenchmarkSuite:
    """Test benchmark suite functionality."""

    @pytest.mark.asyncio
    async def test_run_all_benchmarks(self, benchmark_config):
        """Test running all benchmarks."""
        suite = BenchmarkSuite()

        # Add benchmarks
        suite.add_benchmark(APIBenchmark(benchmark_config))
        suite.add_benchmark(WebSocketBenchmark(benchmark_config))
        suite.add_benchmark(DatabaseBenchmark(benchmark_config))
        suite.add_benchmark(CacheBenchmark(benchmark_config))

        # Run all benchmarks
        results = await suite.run_all()

        # Verify results
        assert len(results) == 4
        for result in results:
            assert result.duration_seconds > 0
            assert result.operations_count > 0

    @pytest.mark.asyncio
    async def test_load_test(self):
        """Test load test functionality."""
        suite = BenchmarkSuite()

        config = BenchmarkConfig(
            test_name="load_test",
            duration_seconds=2,
            concurrent_users=5,
        )

        results = await suite.run_load_test(config, test_duration=2)

        # Verify load test results
        assert "start_time" in results
        assert "end_time" in results
        assert "duration" in results
        assert "total_requests" in results
        assert "successful_requests" in results
        assert "failed_requests" in results
        assert "avg_latency" in results
        assert "p50_latency" in results
        assert "p95_latency" in results
        assert "success_rate" in results

        # Basic sanity checks
        assert results["total_requests"] > 0
        assert results["successful_requests"] >= 0
        assert results["failed_requests"] >= 0
        assert 0 <= results["success_rate"] <= 1
        assert results["avg_latency"] > 0

    @pytest.mark.asyncio
    async def test_benchmark_percentile_calculation(self):
        """Test percentile calculation in benchmarks."""
        suite = BenchmarkSuite()

        # Test with known data
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        p50 = suite._percentile(data, 50)
        p95 = suite._percentile(data, 95)
        p99 = suite._percentile(data, 99)

        # Verify percentiles
        assert p50 == 5.5
        assert p95 == 9.5
        assert p99 == 9.9

    def test_benchmark_report_generation(self):
        """Test benchmark report generation."""
        from app.progress.performance_benchmark import BenchmarkResult

        # Create sample results
        results = [
            BenchmarkResult(
                benchmark_type=BenchmarkType.API_LATENCY,
                test_name="api_test",
                duration_seconds=10.0,
                operations_count=1000,
                operations_per_second=100.0,
                latency_ms=50.0,
                p50_latency_ms=45.0,
                p95_latency_ms=60.0,
                p99_latency_ms=65.0,
                min_latency_ms=30.0,
                max_latency_ms=80.0,
                success_rate=0.99,
                error_count=10,
                memory_usage_mb=100.0,
                cpu_usage_percent=50.0,
            )
        ]

        # Generate report
        report = BenchmarkReporter.generate_report(results)

        # Verify report contains expected content
        assert "api_test" in report
        assert "api_latency" in report
        assert "10.00s" in report
        assert "1000" in report
        assert "50.00ms" in report
        assert "99.00%" in report

    def test_benchmark_json_export(self):
        """Test benchmark JSON export."""
        from app.progress.performance_benchmark import BenchmarkResult

        # Create sample results
        results = [
            BenchmarkResult(
                benchmark_type=BenchmarkType.WEBSOCKET_MESSAGES,
                test_name="ws_test",
                duration_seconds=5.0,
                operations_count=500,
                operations_per_second=100.0,
                latency_ms=10.0,
                p50_latency_ms=9.0,
                p95_latency_ms=12.0,
                p99_latency_ms=13.0,
                min_latency_ms=5.0,
                max_latency_ms=20.0,
                success_rate=0.95,
                error_count=25,
                memory_usage_mb=80.0,
                cpu_usage_percent=30.0,
            )
        ]

        # Export as JSON
        json_data = BenchmarkReporter.export_json(results)

        # Verify JSON structure
        import json
        data = json.loads(json_data)
        assert len(data) == 1
        assert data[0]["test_name"] == "ws_test"
        assert data[0]["benchmark_type"] == "websocket_messages"
        assert data[0]["duration_seconds"] == 5.0


# ============================================================================
# Performance Dashboard Tests
# ============================================================================

class TestPerformanceDashboard:
    """Test performance dashboard functionality."""

    @pytest.mark.asyncio
    async def test_dashboard_start_stop(self, performance_dashboard):
        """Test dashboard start and stop."""
        # Dashboard is already started by fixture
        # Verify it's working by checking custom metrics
        performance_dashboard.increment_counter("test_counter", 10)
        performance_dashboard.set_gauge("test_gauge", 100)
        performance_dashboard.record_timer("test_timer", 50)

        # Check that metrics were recorded
        assert performance_dashboard.custom_counters["test_counter"] == 10
        assert performance_dashboard.custom_gauges["test_gauge"] == 100
        assert "test_timer" in performance_dashboard.custom_timers

    @pytest.mark.asyncio
    async def test_custom_metrics(self, performance_dashboard):
        """Test custom metric recording."""
        # Test counter
        performance_dashboard.increment_counter("hits", 5)
        performance_dashboard.increment_counter("hits", 3)

        assert performance_dashboard.custom_counters["hits"] == 8

        # Test gauge
        performance_dashboard.set_gauge("temperature", 25.5)
        assert performance_dashboard.custom_gauges["temperature"] == 25.5

        # Test timer
        performance_dashboard.record_timer("response_time", 100)
        performance_dashboard.record_timer("response_time", 200)

        assert len(performance_dashboard.custom_timers["response_time"]) == 2

    @pytest.mark.asyncio
    async def test_dashboard_data(self, performance_dashboard):
        """Test dashboard data collection."""
        # Add some metrics
        performance_dashboard.increment_counter("requests", 10)
        performance_dashboard.set_gauge("cpu_temp", 60)
        performance_dashboard.record_timer("db_query", 50)

        # Get dashboard data
        data = performance_dashboard.get_dashboard_data()

        # Verify structure
        assert "timestamp" in data
        assert "system" in data
        assert "custom" in data
        assert "alerts" in data
        assert "metrics_count" in data

        # Verify system metrics
        assert "cpu" in data["system"]
        assert "memory" in data["system"]
        assert "disk" in data["system"]
        assert "process" in data["system"]

        # Verify custom metrics
        assert "counters" in data["custom"]
        assert "gauges" in data["custom"]
        assert "timers" in data["custom"]

        # Verify alerts
        assert "active_alerts" in data["alerts"]
        assert "recent_alerts" in data["alerts"]

    @pytest.mark.asyncio
    async def test_historical_data(self, performance_dashboard):
        """Test historical data retrieval."""
        # Add some metrics
        performance_dashboard.set_gauge("temperature", 25)

        # Get historical data
        history = performance_dashboard.get_historical_data("custom.gauge.temperature", 60)

        # Verify structure
        assert isinstance(history, list)
        if history:
            assert "timestamp" in history[0]
            assert "value" in history[0]

    @pytest.mark.asyncio
    async def test_alert_management(self, performance_dashboard):
        """Test alert management."""
        # Add an alert
        performance_dashboard.add_alert(
            alert_id="high_cpu",
            name="High CPU Usage",
            condition="system.cpu.usage.percent",
            threshold=80.0,
            severity=AlertSeverity.WARNING,
        )

        # Check that alert was added
        assert "high_cpu" in performance_dashboard.alert_manager.alerts

        # Get active alerts
        active_alerts = performance_dashboard.alert_manager.get_active_alerts()
        assert isinstance(active_alerts, list)


# ============================================================================
# Integration Tests
# ============================================================================

class TestPerformanceIntegration:
    """Test integration between performance components."""

    @pytest.mark.asyncio
    async def test_full_performance_test(self, benchmark_config):
        """Test complete performance testing workflow."""
        # Create dashboard
        dashboard = PerformanceDashboard()
        await dashboard.start(system_interval=1.0, alert_interval=2.0)

        try:
            # Add custom metrics
            dashboard.increment_counter("api_requests", 100)
            dashboard.set_gauge("active_connections", 50)
            dashboard.record_timer("request_latency", 45)

            # Create benchmark suite
            suite = BenchmarkSuite()
            suite.add_benchmark(APIBenchmark(benchmark_config))

            # Run benchmark
            results = await suite.run_all()

            # Verify integration
            assert len(results) == 1

            # Check dashboard data
            dashboard_data = dashboard.get_dashboard_data()
            assert dashboard_data["metrics_count"] > 0

        finally:
            await dashboard.stop()

    @pytest.mark.asyncio
    async def test_performance_with_load(self):
        """Test performance under load."""
        # Create dashboard
        dashboard = PerformanceDashboard()
        await dashboard.start()

        try:
            # Simulate load
            start_time = time.time()
            request_count = 0

            while time.time() - start_time < 2:  # Run for 2 seconds
                dashboard.increment_counter("load_requests", 1)
                dashboard.record_timer("load_response", 10 + request_count % 20)
                request_count += 1
                await asyncio.sleep(0.01)  # 100 requests per second

            # Check dashboard data
            dashboard_data = dashboard.get_dashboard_data()

            # Verify metrics
            assert dashboard_data["custom"]["counters"]["load_requests"] > 0
            assert "load_response" in dashboard_data["custom"]["timers"]

        finally:
            await dashboard.stop()


# ============================================================================
# Stress Tests
# ============================================================================

class TestStressTests:
    """Test system behavior under stress."""

    @pytest.mark.asyncio
    async def test_high_concurrency(self):
        """Test system under high concurrency."""
        dashboard = PerformanceDashboard()
        await dashboard.start()

        try:
            # Simulate high concurrency
            tasks = []
            for i in range(100):
                task = asyncio.create_task(
                    dashboard.increment_counter(f"concurrent_req_{i % 10}", 1)
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Check that all metrics were recorded
            dashboard_data = dashboard.get_dashboard_data()
            assert dashboard_data["metrics_count"] > 0

        finally:
            await dashboard.stop()

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage during performance testing."""
        dashboard = PerformanceDashboard()
        await dashboard.start()

        try:
            # Generate many metrics
            for i in range(1000):
                dashboard.increment_counter("memory_test", 1)
                dashboard.set_gauge("memory_test_gauge", i)
                dashboard.record_timer("memory_test_timer", i % 100)

            # Get memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            # Verify memory is within reasonable bounds (< 500MB)
            assert memory_mb < 500

            # Check dashboard data
            dashboard_data = dashboard.get_dashboard_data()
            assert dashboard_data["metrics_count"] > 0

        finally:
            await dashboard.stop()

    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """Test sustained load over time."""
        dashboard = PerformanceDashboard()
        await dashboard.start()

        try:
            # Run sustained load
            start_time = time.time()
            duration = 3  # seconds

            while time.time() - start_time < duration:
                dashboard.increment_counter("sustained_load", 1)
                await asyncio.sleep(0.1)  # 10 requests per second

            # Verify load was sustained
            dashboard_data = dashboard.get_dashboard_data()
            assert dashboard_data["custom"]["counters"]["sustained_load"] >= (duration * 10 * 0.8)  # Allow 20% variance

        finally:
            await dashboard.stop()


# ============================================================================
# Performance Benchmarks
# ============================================================================

class TestPerformanceBenchmarks:
    """Test performance benchmarks against thresholds."""

    @pytest.mark.asyncio
    async def test_api_latency_threshold(self, benchmark_config):
        """Test API latency is within acceptable threshold."""
        benchmark = APIBenchmark(benchmark_config)
        result = await benchmark.run()

        # API latency should be < 100ms
        assert result.latency_ms < 100
        assert result.p95_latency_ms < 150

    @pytest.mark.asyncio
    async def test_cache_performance_threshold(self, benchmark_config):
        """Test cache performance is within acceptable threshold."""
        benchmark = CacheBenchmark(benchmark_config)
        result = await benchmark.run()

        # Cache operations should be < 10ms
        assert result.latency_ms < 10
        assert result.p95_latency_ms < 20

    @pytest.mark.asyncio
    async def test_websocket_performance_threshold(self, benchmark_config):
        """Test WebSocket performance is within acceptable threshold."""
        benchmark = WebSocketBenchmark(benchmark_config)
        result = await benchmark.run()

        # WebSocket latency should be < 50ms
        assert result.latency_ms < 50
        assert result.p95_latency_ms < 100

    @pytest.mark.asyncio
    async def test_success_rate_threshold(self, benchmark_config):
        """Test success rate is within acceptable threshold."""
        benchmark = APIBenchmark(benchmark_config)
        result = await benchmark.run()

        # Success rate should be > 95%
        assert result.success_rate >= 0.95

    @pytest.mark.asyncio
    async def test_throughput_threshold(self, benchmark_config):
        """Test throughput is within acceptable threshold."""
        benchmark = APIBenchmark(benchmark_config)
        result = await benchmark.run()

        # Should handle at least 50 operations per second
        assert result.operations_per_second >= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
