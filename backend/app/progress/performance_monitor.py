"""Real-time performance monitoring dashboard.

This module provides real-time monitoring capabilities including:
- System metrics collection
- Application metrics tracking
- Performance alerts
- Real-time dashboards
- Historical data storage
"""

import asyncio
import time
import logging
import psutil
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from threading import Lock
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


@dataclass
class Alert:
    """Alert definition."""
    id: str
    name: str
    severity: AlertSeverity
    condition: str
    threshold: float
    current_value: float
    triggered: bool
    timestamp: float = field(default_factory=time.time)
    description: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and stores metrics."""

    def __init__(self, max_history: int = 10000):
        """Initialize metrics collector.

        Args:
            max_history: Maximum number of metric points to store
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = Lock()

    def record(self, metric: Metric):
        """Record a metric.

        Args:
            metric: Metric to record
        """
        with self._lock:
            self.metrics[metric.name].append(metric)

    def record_counter(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a counter metric.

        Args:
            name: Metric name
            value: Counter value
            labels: Optional labels
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            labels=labels or {},
        )
        self.record(metric)

    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            labels=labels or {},
        )
        self.record(metric)

    def record_timer(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a timer metric.

        Args:
            name: Metric name
            value: Timer value
            labels: Optional labels
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.TIMER,
            labels=labels or {},
        )
        self.record(metric)

    def get_metrics(self, name: Optional[str] = None, since: Optional[float] = None) -> List[Metric]:
        """Get metrics.

        Args:
            name: Optional metric name filter
            since: Optional timestamp filter

        Returns:
            List of metrics
        """
        with self._lock:
            if name:
                metrics = list(self.metrics.get(name, []))
            else:
                metrics = []
                for metric_deque in self.metrics.values():
                    metrics.extend(metric_deque)

            if since:
                metrics = [m for m in metrics if m.timestamp >= since]

            return metrics

    def get_latest_value(self, name: str, default: float = 0.0) -> float:
        """Get latest value for metric.

        Args:
            name: Metric name
            default: Default value if metric not found

        Returns:
            Latest metric value
        """
        with self._lock:
            metrics = self.metrics.get(name, [])
            return metrics[-1].value if metrics else default

    def get_average_value(self, name: str, since: Optional[float] = None) -> float:
        """Get average value for metric.

        Args:
            name: Metric name
            since: Optional timestamp filter

        Returns:
            Average metric value
        """
        metrics = self.get_metrics(name, since)
        if not metrics:
            return 0.0

        values = [m.value for m in metrics]
        return sum(values) / len(values)


class SystemMonitor:
    """Monitors system resource usage."""

    def __init__(self, collector: MetricsCollector):
        """Initialize system monitor.

        Args:
            collector: Metrics collector
        """
        self.collector = collector
        self._monitoring = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, interval: float = 5.0):
        """Start system monitoring.

        Args:
            interval: Monitoring interval in seconds
        """
        self._monitoring = True
        self._task = asyncio.create_task(self._monitor_loop(interval))
        logger.info("System monitoring started")

    async def stop(self):
        """Stop system monitoring."""
        self._monitoring = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")

    async def _monitor_loop(self, interval: float):
        """System monitoring loop.

        Args:
            interval: Monitoring interval
        """
        while self._monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.collector.record_gauge("system.cpu.usage.percent", cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.collector.record_gauge("system.memory.usage.percent", memory.percent)
                self.collector.record_gauge("system.memory.available.bytes", memory.available)
                self.collector.record_gauge("system.memory.used.bytes", memory.used)

                # Disk usage
                disk = psutil.disk_usage('/')
                self.collector.record_gauge("system.disk.usage.percent", disk.percent)
                self.collector.record_gauge("system.disk.free.bytes", disk.free)
                self.collector.record_gauge("system.disk.used.bytes", disk.used)

                # Network I/O
                network = psutil.net_io_counters()
                if network:
                    self.collector.record_counter("system.network.bytes_sent", network.bytes_sent)
                    self.collector.record_counter("system.network.bytes_recv", network.bytes_recv)

                # Process info
                process = psutil.Process()
                self.collector.record_gauge("process.cpu.usage.percent", process.cpu_percent())
                self.collector.record_gauge("process.memory.usage.mb", process.memory_info().rss / 1024 / 1024)
                self.collector.record_gauge("process.threads.count", process.num_threads())

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")


class AlertManager:
    """Manages performance alerts."""

    def __init__(self, collector: MetricsCollector):
        """Initialize alert manager.

        Args:
            collector: Metrics collector
        """
        self.collector = collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self._lock = Lock()

    def add_alert(self, alert: Alert):
        """Add an alert.

        Args:
            alert: Alert to add
        """
        with self._lock:
            self.alerts[alert.id] = alert
            logger.info(f"Added alert: {alert.name}")

    async def check_alerts(self):
        """Check all alerts against current metrics.

        Returns:
            List of triggered alerts
        """
        triggered = []

        with self._lock:
            for alert in self.alerts.values():
                current_value = self.collector.get_latest_value(alert.condition)

                # Simple threshold check (can be extended)
                if current_value >= alert.threshold and not alert.triggered:
                    alert.triggered = True
                    alert.current_value = current_value
                    alert.timestamp = time.time()
                    triggered.append(alert)

                    # Add to history
                    self.alert_history.append(alert)

                    # Log alert
                    logger.warning(f"Alert triggered: {alert.name} (value: {current_value}, threshold: {alert.threshold})")

        return triggered

    def reset_alert(self, alert_id: str):
        """Reset an alert.

        Args:
            alert_id: Alert ID
        """
        with self._lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].triggered = False
                logger.info(f"Alert reset: {alert_id}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts.

        Returns:
            List of active alerts
        """
        with self._lock:
            return [alert for alert in self.alerts.values() if alert.triggered]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of historical alerts
        """
        with self._lock:
            return list(self.alert_history)[-limit:]


class PerformanceDashboard:
    """Real-time performance dashboard."""

    def __init__(self):
        """Initialize performance dashboard."""
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector)

        # Custom metrics
        self.custom_counters: Dict[str, float] = defaultdict(float)
        self.custom_gauges: Dict[str, float] = {}
        self.custom_timers: Dict[str, List[float]] = defaultdict(list)

        # Background tasks
        self._monitoring = False
        self._alert_check_task: Optional[asyncio.Task] = None

    async def start(self, system_interval: float = 5.0, alert_interval: float = 10.0):
        """Start the performance dashboard.

        Args:
            system_interval: System monitoring interval
            alert_interval: Alert check interval
        """
        # Start system monitoring
        await self.system_monitor.start(system_interval)

        # Start alert checking
        self._monitoring = True
        self._alert_check_task = asyncio.create_task(self._alert_check_loop(alert_interval))

        logger.info("Performance dashboard started")

    async def stop(self):
        """Stop the performance dashboard."""
        self._monitoring = False

        # Stop system monitoring
        await self.system_monitor.stop()

        # Stop alert checking
        if self._alert_check_task:
            self._alert_check_task.cancel()
            try:
                await self._alert_check_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance dashboard stopped")

    async def _alert_check_loop(self, interval: float):
        """Alert checking loop.

        Args:
            interval: Check interval
        """
        while self._monitoring:
            try:
                await self.alert_manager.check_alerts()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert checking: {e}")

    # Custom metric methods

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a custom counter.

        Args:
            name: Counter name
            value: Increment value
            labels: Optional labels
        """
        self.custom_counters[name] += value
        self.metrics_collector.record_counter(f"custom.counter.{name}", self.custom_counters[name], labels)

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a custom gauge.

        Args:
            name: Gauge name
            value: Gauge value
            labels: Optional labels
        """
        self.custom_gauges[name] = value
        self.metrics_collector.record_gauge(f"custom.gauge.{name}", value, labels)

    def record_timer(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a custom timer.

        Args:
            name: Timer name
            value: Timer value
            labels: Optional labels
        """
        self.custom_timers[name].append(value)
        # Keep only last 1000 values
        if len(self.custom_timers[name]) > 1000:
            self.custom_timers[name] = self.custom_timers[name][-1000:]

        self.metrics_collector.record_timer(f"custom.timer.{name}", value, labels)

    # Dashboard data methods

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data.

        Returns:
            Dashboard data
        """
        now = time.time()

        # System metrics
        system_data = {
            "cpu": {
                "usage_percent": self.metrics_collector.get_latest_value("system.cpu.usage.percent"),
            },
            "memory": {
                "usage_percent": self.metrics_collector.get_latest_value("system.memory.usage.percent"),
                "available_bytes": self.metrics_collector.get_latest_value("system.memory.available.bytes"),
                "used_bytes": self.metrics_collector.get_latest_value("system.memory.used.bytes"),
            },
            "disk": {
                "usage_percent": self.metrics_collector.get_latest_value("system.disk.usage.percent"),
                "free_bytes": self.metrics_collector.get_latest_value("system.disk.free.bytes"),
                "used_bytes": self.metrics_collector.get_latest_value("system.disk.used.bytes"),
            },
            "process": {
                "cpu_usage_percent": self.metrics_collector.get_latest_value("process.cpu.usage.percent"),
                "memory_usage_mb": self.metrics_collector.get_latest_value("process.memory.usage.mb"),
                "threads_count": self.metrics_collector.get_latest_value("process.threads.count"),
            },
        }

        # Custom metrics
        custom_data = {
            "counters": dict(self.custom_counters),
            "gauges": dict(self.custom_gauges),
            "timers": {
                name: {
                    "count": len(values),
                    "average": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                }
                for name, values in self.custom_timers.items()
            },
        }

        # Alerts
        alerts_data = {
            "active_alerts": [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "value": alert.current_value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp,
                }
                for alert in self.alert_manager.get_active_alerts()
            ],
            "recent_alerts": [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "timestamp": alert.timestamp,
                }
                for alert in self.alert_manager.get_alert_history(10)
            ],
        }

        return {
            "timestamp": now,
            "system": system_data,
            "custom": custom_data,
            "alerts": alerts_data,
            "metrics_count": len(self.metrics_collector.metrics),
        }

    def get_historical_data(self, metric_name: str, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get historical data for a metric.

        Args:
            metric_name: Metric name
            duration_minutes: Duration in minutes

        Returns:
            Historical data points
        """
        since = time.time() - (duration_minutes * 60)
        metrics = self.metrics_collector.get_metrics(metric_name, since)

        return [
            {
                "timestamp": m.timestamp,
                "value": m.value,
                "labels": m.labels,
            }
            for m in metrics
        ]

    def add_alert(
        self,
        alert_id: str,
        name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity = AlertSeverity.WARNING,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Add a new alert.

        Args:
            alert_id: Alert ID
            name: Alert name
            condition: Metric condition to check
            threshold: Threshold value
            severity: Alert severity
            description: Alert description
            labels: Optional labels
        """
        alert = Alert(
            id=alert_id,
            name=name,
            severity=severity,
            condition=condition,
            threshold=threshold,
            current_value=0.0,
            triggered=False,
            description=description,
            labels=labels or {},
        )

        self.alert_manager.add_alert(alert)


# Global performance dashboard instance
performance_dashboard = PerformanceDashboard()
