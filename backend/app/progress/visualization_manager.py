"""Visualization management for real-time progress tracking.

This module provides VisualizationManager for creating charts, dashboards,
and visual representations of progress tracking data.
"""

import asyncio
import logging
import time
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text

from .models.task import TaskProgress, TaskStatus
from .models.log import TaskLog, LogLevel
from .models.metric import ProgressMetric
from .models.notification import Notification, NotificationType
from .schemas.progress_operations import (
    VisualizationQuery,
    DashboardQuery,
)
from .utils.formatters import (
    format_percentage,
    format_duration,
    format_number,
    format_timestamp,
)
from .progress_manager import progress_manager
from .log_manager import log_manager
from .notification_manager import notification_manager
from .event_bus import event_bus
from .websocket import websocket_manager

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Types of visualization charts."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    TABLE = "table"


class MetricAggregation(Enum):
    """Metric aggregation methods."""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    MEDIAN = "median"


class ChartTemplate:
    """Predefined chart template."""

    def __init__(
        self,
        template_id: str,
        name: str,
        chart_type: ChartType,
        config: Dict[str, Any],
        description: str = "",
    ):
        """Initialize chart template.

        Args:
            template_id: Template ID
            name: Template name
            chart_type: Type of chart
            config: Chart configuration
            description: Template description
        """
        self.template_id = template_id
        self.name = name
        self.chart_type = chart_type
        self.config = config
        self.description = description
        self.created_at = datetime.utcnow()


@dataclass
class RealTimeUpdate:
    """Real-time update configuration."""

    connection_id: str
    visualization_id: str
    update_interval: float
    last_update: float
    filters: Dict[str, Any]
    callback: Optional[Callable] = None


class VisualizationData:
    """Container for visualization data."""

    def __init__(
        self,
        chart_type: ChartType,
        title: str,
        data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize visualization data.

        Args:
            chart_type: Type of chart
            title: Chart title
            data: Chart data points
            metadata: Additional metadata
        """
        self.chart_type = chart_type
        self.title = title
        self.data = data
        self.metadata = metadata or {}
        self.generated_at = datetime.utcnow()


class DashboardWidget:
    """Represents a dashboard widget."""

    def __init__(
        self,
        widget_id: str,
        title: str,
        chart_type: ChartType,
        query: VisualizationQuery,
        position: Dict[str, int],
        size: Dict[str, int],
    ):
        """Initialize dashboard widget.

        Args:
            widget_id: Widget ID
            title: Widget title
            chart_type: Type of chart
            query: Data query
            position: Widget position (x, y)
            size: Widget size (width, height)
        """
        self.widget_id = widget_id
        self.title = title
        self.chart_type = chart_type
        self.query = query
        self.position = position
        self.size = size
        self.created_at = datetime.utcnow()
        self.last_updated: Optional[datetime] = None


class VisualizationManager:
    """Core manager for data visualization and dashboards."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize visualization manager.

        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db_session = db_session
        self.dashboard_widgets: Dict[str, DashboardWidget] = {}
        self.chart_templates: Dict[str, ChartTemplate] = {}
        self.real_time_updates: Dict[str, RealTimeUpdate] = {}
        self._stats = {
            "total_visualizations_created": 0,
            "total_dashboards_created": 0,
            "total_data_points_rendered": 0,
            "total_templates_created": 0,
            "total_real_time_subscriptions": 0,
            "by_chart_type": defaultdict(int),
        }

        # Load default templates
        self._load_default_templates()

    async def create_progress_chart(
        self,
        task_ids: List[str],
        time_range: Optional[str] = None,
        group_by: Optional[str] = None,
        aggregation: MetricAggregation = MetricAggregation.AVG,
        db_session: Optional[Session] = None,
    ) -> VisualizationData:
        """Create progress tracking chart.

        Args:
            task_ids: List of task IDs to include
            time_range: Time range filter (e.g., "1d", "7d", "30d")
            group_by: Group by field (e.g., "status", "task_type")
            aggregation: Aggregation method
            db_session: Database session (overrides instance session)

        Returns:
            VisualizationData instance
        """
        session = db_session or self.db_session
        if not session:
            # Generate mock data for testing
            data = self._generate_mock_progress_data(task_ids)
        else:
            # Query real data
            query = session.query(TaskProgress)

            # Apply filters
            query = query.filter(TaskProgress.task_id.in_(task_ids))

            if time_range:
                cutoff = self._parse_time_range(time_range)
                query = query.filter(TaskProgress.updated_at >= cutoff)

            # Group and aggregate
            if group_by:
                data = await self._aggregate_progress_by_group(
                    query, group_by, aggregation
                )
            else:
                data = await self._aggregate_progress_data(query, aggregation)

        visualization = VisualizationData(
            chart_type=ChartType.LINE,
            title="Task Progress Over Time",
            data=data,
            metadata={
                "task_ids": task_ids,
                "time_range": time_range,
                "group_by": group_by,
                "aggregation": aggregation.value,
            },
        )

        self._stats["total_visualizations_created"] += 1
        self._stats["by_chart_type"][ChartType.LINE.value] += 1
        self._stats["total_data_points_rendered"] += len(data)

        return visualization

    async def create_status_distribution_chart(
        self,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
        db_session: Optional[Session] = None,
    ) -> VisualizationData:
        """Create task status distribution chart.

        Args:
            user_id: Filter by user ID (optional)
            task_type: Filter by task type (optional)
            db_session: Database session (overrides instance session)

        Returns:
            VisualizationData instance
        """
        session = db_session or self.db_session
        if not session:
            # Generate mock data
            data = [
                {"status": "completed", "count": 45, "percentage": 60},
                {"status": "running", "count": 20, "percentage": 27},
                {"status": "failed", "count": 5, "percentage": 7},
                {"status": "paused", "count": 5, "percentage": 7},
            ]
        else:
            # Query real data
            query = session.query(TaskProgress.status, func.count(TaskProgress.id))

            if user_id:
                query = query.filter(TaskProgress.user_id == user_id)
            if task_type:
                query = query.filter(TaskProgress.task_type == task_type)

            query = query.group_by(TaskProgress.status)

            results = query.all()
            total = sum(count for _, count in results)

            data = [
                {
                    "status": status,
                    "count": count,
                    "percentage": (count / total * 100) if total > 0 else 0,
                }
                for status, count in results
            ]

        visualization = VisualizationData(
            chart_type=ChartType.PIE,
            title="Task Status Distribution",
            data=data,
            metadata={
                "user_id": user_id,
                "task_type": task_type,
                "total_tasks": sum(item["count"] for item in data),
            },
        )

        self._stats["total_visualizations_created"] += 1
        self._stats["by_chart_type"][ChartType.PIE.value] += 1
        self._stats["total_data_points_rendered"] += len(data)

        return visualization

    async def create_performance_metrics_chart(
        self,
        task_ids: List[str],
        time_range: str = "7d",
        db_session: Optional[Session] = None,
    ) -> VisualizationData:
        """Create performance metrics chart.

        Args:
            task_ids: List of task IDs
            time_range: Time range filter
            db_session: Database session (overrides instance session)

        Returns:
            VisualizationData instance
        """
        session = db_session or self.db_session
        if not session:
            # Generate mock data
            data = [
                {"metric": "avg_duration", "value": 3600, "unit": "seconds"},
                {"metric": "success_rate", "value": 92.5, "unit": "percentage"},
                {"metric": "avg_retries", "value": 1.2, "unit": "count"},
                {"metric": "throughput", "value": 45, "unit": "tasks/hour"},
            ]
        else:
            # Query real metrics
            cutoff = self._parse_time_range(time_range)

            # Get task metrics
            tasks = (
                session.query(TaskProgress)
                .filter(
                    TaskProgress.task_id.in_(task_ids),
                    TaskProgress.updated_at >= cutoff,
                )
                .all()
            )

            if not tasks:
                data = []
            else:
                total_duration = sum(
                    t.duration_seconds or 0 for t in tasks if t.duration_seconds
                )
                completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
                success_rate = (
                    len(completed_tasks) / len(tasks) * 100 if tasks else 0
                )

                data = [
                    {
                        "metric": "total_tasks",
                        "value": len(tasks),
                        "unit": "count",
                    },
                    {
                        "metric": "avg_duration",
                        "value": total_duration / len(tasks) if tasks else 0,
                        "unit": "seconds",
                    },
                    {
                        "metric": "success_rate",
                        "value": success_rate,
                        "unit": "percentage",
                    },
                    {
                        "metric": "completed_tasks",
                        "value": len(completed_tasks),
                        "unit": "count",
                    },
                ]

        visualization = VisualizationData(
            chart_type=ChartType.GAUGE,
            title="Performance Metrics",
            data=data,
            metadata={
                "task_ids": task_ids,
                "time_range": time_range,
            },
        )

        self._stats["total_visualizations_created"] += 1
        self._stats["by_chart_type"][ChartType.GAUGE.value] += 1
        self._stats["total_data_points_rendered"] += len(data)

        return visualization

    async def create_activity_heatmap(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
        db_session: Optional[Session] = None,
    ) -> VisualizationData:
        """Create activity heatmap.

        Args:
            user_id: Filter by user ID (optional)
            days: Number of days to include
            db_session: Database session (overrides instance session)

        Returns:
            VisualizationData instance
        """
        session = db_session or self.db_session
        if not session:
            # Generate mock data
            data = self._generate_mock_heatmap_data(days)
        else:
            # Query real data
            cutoff = datetime.utcnow() - timedelta(days=days)

            query = session.query(
                func.date(TaskProgress.created_at),
                func.count(TaskProgress.id),
            ).filter(TaskProgress.created_at >= cutoff)

            if user_id:
                query = query.filter(TaskProgress.user_id == user_id)

            query = query.group_by(func.date(TaskProgress.created_at))

            results = query.all()

            data = [
                {
                    "date": date.isoformat(),
                    "count": count,
                    "weekday": date.weekday(),
                }
                for date, count in results
            ]

        visualization = VisualizationData(
            chart_type=ChartType.HEATMAP,
            title="Activity Heatmap",
            data=data,
            metadata={
                "user_id": user_id,
                "days": days,
            },
        )

        self._stats["total_visualizations_created"] += 1
        self._stats["by_chart_type"][ChartType.HEATMAP.value] += 1
        self._stats["total_data_points_rendered"] += len(data)

        return visualization

    async def create_dashboard(
        self,
        dashboard_id: str,
        title: str,
        widgets: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create a dashboard with multiple widgets.

        Args:
            dashboard_id: Dashboard ID
            title: Dashboard title
            widgets: List of widget configurations

        Returns:
            Dashboard configuration
        """
        dashboard = {
            "dashboard_id": dashboard_id,
            "title": title,
            "widgets": [],
            "created_at": datetime.utcnow().isoformat(),
        }

        for widget_config in widgets:
            widget = DashboardWidget(
                widget_id=widget_config["widget_id"],
                title=widget_config["title"],
                chart_type=ChartType(widget_config["chart_type"]),
                query=VisualizationQuery(**widget_config["query"]),
                position=widget_config["position"],
                size=widget_config["size"],
            )

            self.dashboard_widgets[widget.widget_id] = widget
            dashboard["widgets"].append({
                "widget_id": widget.widget_id,
                "title": widget.title,
                "chart_type": widget.chart_type.value,
                "position": widget.position,
                "size": widget.size,
            })

        self._stats["total_dashboards_created"] += 1

        logger.info(f"Created dashboard {dashboard_id} with {len(widgets)} widgets")
        return dashboard

    async def get_dashboard_data(
        self,
        dashboard_id: str,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Get dashboard data for all widgets.

        Args:
            dashboard_id: Dashboard ID
            db_session: Database session (overrides instance session)

        Returns:
            Dashboard with populated data
        """
        dashboard_widgets = [
            widget for widget in self.dashboard_widgets.values()
            if widget.widget_id.startswith(dashboard_id)
        ]

        if not dashboard_widgets:
            return {"error": "Dashboard not found"}

        dashboard_data = {
            "dashboard_id": dashboard_id,
            "widgets": [],
            "generated_at": datetime.utcnow().isoformat(),
        }

        for widget in dashboard_widgets:
            try:
                # Generate visualization based on widget query
                if widget.query.task_ids:
                    viz_data = await self.create_progress_chart(
                        widget.query.task_ids,
                        widget.query.time_range,
                        widget.query.group_by,
                        MetricAggregation(widget.query.aggregation),
                        db_session,
                    )
                else:
                    viz_data = await self.create_status_distribution_chart(
                        widget.query.user_id,
                        widget.query.task_type,
                        db_session,
                    )

                dashboard_data["widgets"].append({
                    "widget_id": widget.widget_id,
                    "title": widget.title,
                    "chart_type": widget.chart_type.value,
                    "data": viz_data.data,
                    "metadata": viz_data.metadata,
                    "position": widget.position,
                    "size": widget.size,
                })

            except Exception as e:
                logger.error(f"Error generating widget {widget.widget_id}: {e}")
                dashboard_data["widgets"].append({
                    "widget_id": widget.widget_id,
                    "title": widget.title,
                    "error": str(e),
                })

        return dashboard_data

    async def export_visualization(
        self,
        visualization: VisualizationData,
        format: str = "json",
    ) -> Union[str, Dict[str, Any]]:
        """Export visualization data.

        Args:
            visualization: VisualizationData instance
            format: Export format (json, csv)

        Returns:
            Exported data as string or dict
        """
        export_data = {
            "chart_type": visualization.chart_type.value,
            "title": visualization.title,
            "data": visualization.data,
            "metadata": visualization.metadata,
            "generated_at": visualization.generated_at.isoformat(),
        }

        if format == "json":
            return export_data
        elif format == "csv":
            # Convert to CSV format
            if not visualization.data:
                return ""

            headers = visualization.data[0].keys()
            csv_lines = [",".join(headers)]

            for item in visualization.data:
                values = [str(item.get(header, "")) for header in headers]
                csv_lines.append(",".join(values))

            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def _aggregate_progress_data(
        self,
        query,
        aggregation: MetricAggregation,
    ) -> List[Dict[str, Any]]:
        """Aggregate progress data.

        Args:
            query: SQLAlchemy query
            aggregation: Aggregation method

        Returns:
            Aggregated data points
        """
        # This is a simplified version - in practice you'd need more complex logic
        tasks = query.all()

        if aggregation == MetricAggregation.AVG:
            avg_progress = sum(t.progress for t in tasks) / len(tasks) if tasks else 0
            return [{"time": datetime.utcnow().isoformat(), "value": avg_progress}]

        return []

    async def _aggregate_progress_by_group(
        self,
        query,
        group_by: str,
        aggregation: MetricAggregation,
    ) -> List[Dict[str, Any]]:
        """Aggregate progress data by group.

        Args:
            query: SQLAlchemy query
            group_by: Field to group by
            aggregation: Aggregation method

        Returns:
            Aggregated data points by group
        """
        # Simplified implementation
        tasks = query.all()

        if group_by == "status":
            grouped = defaultdict(list)
            for task in tasks:
                grouped[task.status].append(task)

            return [
                {
                    "group": status,
                    "value": sum(t.progress for t in group) / len(group) if group else 0,
                    "count": len(group),
                }
                for status, group in grouped.items()
            ]

        return []

    def _parse_time_range(self, time_range: str) -> datetime:
        """Parse time range string to datetime.

        Args:
            time_range: Time range string (e.g., "1d", "7d", "30d")

        Returns:
            datetime cutoff
        """
        now = datetime.utcnow()

        if time_range.endswith("d"):
            days = int(time_range[:-1])
            return now - timedelta(days=days)
        elif time_range.endswith("h"):
            hours = int(time_range[:-1])
            return now - timedelta(hours=hours)
        elif time_range.endswith("m"):
            minutes = int(time_range[:-1])
            return now - timedelta(minutes=minutes)

        # Default to 7 days
        return now - timedelta(days=7)

    def _generate_mock_progress_data(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate mock progress data for testing.

        Args:
            task_ids: List of task IDs

        Returns:
            Mock data points
        """
        data = []
        base_time = datetime.utcnow()

        for i in range(24):  # 24 hours of data
            timestamp = base_time - timedelta(hours=23 - i)
            data.append({
                "time": timestamp.isoformat(),
                "value": 50 + (i * 2) + (i % 5) * 5,  # Simulate progress over time
            })

        return data

    def _generate_mock_heatmap_data(self, days: int) -> List[Dict[str, Any]]:
        """Generate mock heatmap data for testing.

        Args:
            days: Number of days

        Returns:
            Mock heatmap data
        """
        data = []
        base_date = datetime.utcnow().date()

        for i in range(days):
            date = base_date - timedelta(days=days - 1 - i)
            data.append({
                "date": date.isoformat(),
                "count": (i % 7) * 3 + (i % 3) * 2,  # Simulate varying activity
                "weekday": date.weekday(),
            })

        return data

    def _load_default_templates(self):
        """Load default chart templates."""
        # Progress timeline template
        self.chart_templates["progress_timeline"] = ChartTemplate(
            template_id="progress_timeline",
            name="Progress Timeline",
            chart_type=ChartType.LINE,
            config={
                "x_axis": "time",
                "y_axis": "progress",
                "color": "#3b82f6",
                "show_grid": True,
                "animate": True,
                "duration": 1000,
            },
            description="Shows task progress over time"
        )

        # Status distribution template
        self.chart_templates["status_distribution"] = ChartTemplate(
            template_id="status_distribution",
            name="Status Distribution",
            chart_type=ChartType.PIE,
            config={
                "show_legend": True,
                "donut": False,
                "colors": ["#10b981", "#f59e0b", "#ef4444", "#6b7280"],
                "animate": True,
                "duration": 800,
            },
            description="Shows distribution of task statuses"
        )

        # Performance metrics template
        self.chart_templates["performance_metrics"] = ChartTemplate(
            template_id="performance_metrics",
            name="Performance Metrics",
            chart_type=ChartType.GAUGE,
            config={
                "min": 0,
                "max": 100,
                "unit": "%",
                "color_ranges": [
                    {"min": 0, "max": 50, "color": "#ef4444"},
                    {"min": 50, "max": 80, "color": "#f59e0b"},
                    {"min": 80, "max": 100, "color": "#10b981"},
                ],
            },
            description="Shows key performance metrics as gauges"
        )

        # Activity heatmap template
        self.chart_templates["activity_heatmap"] = ChartTemplate(
            template_id="activity_heatmap",
            name="Activity Heatmap",
            chart_type=ChartType.HEATMAP,
            config={
                "color_scale": "viridis",
                "show_tooltip": True,
                "cell_size": 15,
            },
            description="Shows activity patterns over time"
        )

        self._stats["total_templates_created"] = len(self.chart_templates)

    async def create_custom_chart(
        self,
        template_id: str,
        data: List[Dict[str, Any]],
        title: str,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> VisualizationData:
        """Create a custom chart using a template.

        Args:
            template_id: Template ID to use
            data: Chart data
            title: Chart title
            custom_config: Custom configuration overrides

        Returns:
            VisualizationData instance
        """
        if template_id not in self.chart_templates:
            raise ValueError(f"Template not found: {template_id}")

        template = self.chart_templates[template_id]
        config = template.config.copy()
        if custom_config:
            config.update(custom_config)

        visualization = VisualizationData(
            chart_type=template.chart_type,
            title=title,
            data=data,
            metadata={
                "template_id": template_id,
                "template_name": template.name,
                "config": config,
            },
        )

        self._stats["total_visualizations_created"] += 1
        self._stats["by_chart_type"][template.chart_type.value] += 1
        self._stats["total_data_points_rendered"] += len(data)

        return visualization

    async def add_real_time_subscription(
        self,
        connection_id: str,
        visualization_query: Dict[str, Any],
        update_interval: float = 5.0,
    ) -> str:
        """Add a real-time update subscription.

        Args:
            connection_id: WebSocket connection ID
            visualization_query: Query parameters for updates
            update_interval: Update interval in seconds

        Returns:
            Subscription ID
        """
        subscription_id = str(uuid4())

        subscription = RealTimeUpdate(
            connection_id=connection_id,
            visualization_id=subscription_id,
            update_interval=update_interval,
            last_update=time.time(),
            filters=visualization_query,
        )

        self.real_time_updates[subscription_id] = subscription
        self._stats["total_real_time_subscriptions"] += 1

        # Start the update task
        asyncio.create_task(self._run_real_time_updates(subscription_id))

        logger.info(f"Added real-time subscription {subscription_id} for connection {connection_id}")
        return subscription_id

    async def remove_real_time_subscription(self, subscription_id: str):
        """Remove a real-time update subscription.

        Args:
            subscription_id: Subscription ID to remove
        """
        if subscription_id in self.real_time_updates:
            del self.real_time_updates[subscription_id]
            self._stats["total_real_time_subscriptions"] = len(self.real_time_updates)
            logger.info(f"Removed real-time subscription {subscription_id}")

    async def _run_real_time_updates(self, subscription_id: str):
        """Run real-time updates for a subscription.

        Args:
            subscription_id: Subscription ID
        """
        while subscription_id in self.real_time_updates:
            subscription = self.real_time_updates[subscription_id]

            try:
                # Check if it's time for an update
                current_time = time.time()
                if current_time - subscription.last_update >= subscription.update_interval:
                    # Generate new visualization data
                    viz_data = await self._generate_realtime_data(subscription.filters)

                    # Send update via WebSocket
                    message = {
                        "type": "visualization_update",
                        "subscription_id": subscription_id,
                        "data": viz_data,
                        "timestamp": current_time,
                    }

                    await websocket_manager.send_message(
                        subscription.connection_id,
                        message
                    )

                    subscription.last_update = current_time

                # Wait before next check
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in real-time updates for {subscription_id}: {e}")
                await asyncio.sleep(5.0)

    async def _generate_realtime_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate real-time visualization data.

        Args:
            filters: Filter parameters

        Returns:
            Visualization data dictionary
        """
        # This is a simplified implementation
        # In practice, you'd query the actual data based on filters

        chart_type = filters.get("chart_type", "line")
        task_ids = filters.get("task_ids", [])

        if chart_type == "line":
            data = [
                {"time": datetime.utcnow().isoformat(), "value": 50 + (time.time() % 100)},
                {"time": (datetime.utcnow() - timedelta(minutes=1)).isoformat(), "value": 48},
                {"time": (datetime.utcnow() - timedelta(minutes=2)).isoformat(), "value": 46},
            ]
        elif chart_type == "pie":
            data = [
                {"status": "completed", "count": 45},
                {"status": "running", "count": 20},
                {"status": "failed", "count": 5},
            ]
        else:
            data = [{"value": 75, "label": "Current"}]

        return {
            "chart_type": chart_type,
            "data": data,
            "filters": filters,
        }

    async def create_animated_chart(
        self,
        base_data: List[Dict[str, Any]],
        animation_config: Dict[str, Any],
    ) -> VisualizationData:
        """Create a chart with animations.

        Args:
            base_data: Base chart data
            animation_config: Animation configuration

        Returns:
            VisualizationData with animation metadata
        """
        # Add animation metadata to visualization
        metadata = {
            "animation": {
                "enabled": True,
                "type": animation_config.get("type", "fade"),
                "duration": animation_config.get("duration", 1000),
                "easing": animation_config.get("easing", "ease-in-out"),
                "stagger": animation_config.get("stagger", 0),
            },
            "transitions": {
                "enabled": True,
                "duration": animation_config.get("transition_duration", 500),
            },
        }

        visualization = VisualizationData(
            chart_type=ChartType.LINE,
            title=animation_config.get("title", "Animated Chart"),
            data=base_data,
            metadata=metadata,
        )

        return visualization

    def add_chart_template(
        self,
        template_id: str,
        name: str,
        chart_type: ChartType,
        config: Dict[str, Any],
        description: str = "",
    ) -> ChartTemplate:
        """Add a custom chart template.

        Args:
            template_id: Template ID
            name: Template name
            chart_type: Type of chart
            config: Chart configuration
            description: Template description

        Returns:
            Created ChartTemplate instance
        """
        template = ChartTemplate(
            template_id=template_id,
            name=name,
            chart_type=chart_type,
            config=config,
            description=description,
        )

        self.chart_templates[template_id] = template
        self._stats["total_templates_created"] += 1

        logger.info(f"Added chart template: {name}")
        return template

    def get_chart_template(self, template_id: str) -> Optional[ChartTemplate]:
        """Get a chart template by ID.

        Args:
            template_id: Template ID

        Returns:
            ChartTemplate instance or None if not found
        """
        return self.chart_templates.get(template_id)

    def list_chart_templates(self) -> List[ChartTemplate]:
        """List all available chart templates.

        Returns:
            List of ChartTemplate instances
        """
        return list(self.chart_templates.values())

    async def export_dashboard(
        self,
        dashboard_id: str,
        format: str = "json",
    ) -> Union[str, Dict[str, Any]]:
        """Export dashboard configuration.

        Args:
            dashboard_id: Dashboard ID to export
            format: Export format (json, yaml)

        Returns:
            Exported dashboard as string or dict
        """
        dashboard_widgets = [
            widget for widget in self.dashboard_widgets.values()
            if widget.widget_id.startswith(dashboard_id)
        ]

        if not dashboard_widgets:
            raise ValueError(f"Dashboard not found: {dashboard_id}")

        dashboard_data = {
            "dashboard_id": dashboard_id,
            "exported_at": datetime.utcnow().isoformat(),
            "widgets": [],
        }

        for widget in dashboard_widgets:
            dashboard_data["widgets"].append({
                "widget_id": widget.widget_id,
                "title": widget.title,
                "chart_type": widget.chart_type.value,
                "position": widget.position,
                "size": widget.size,
                "query": widget.query.dict(),
            })

        if format == "json":
            return json.dumps(dashboard_data, indent=2)
        elif format == "yaml":
            try:
                import yaml
                return yaml.dump(dashboard_data, default_flow_style=False)
            except ImportError:
                raise ValueError("PyYAML not installed")
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_stats(self) -> Dict[str, Any]:
        """Get visualization manager statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            **dict(self._stats),
            "total_widgets": len(self.dashboard_widgets),
            "total_templates": len(self.chart_templates),
            "active_subscriptions": len(self.real_time_updates),
        }


# Global visualization manager instance
visualization_manager = VisualizationManager()
