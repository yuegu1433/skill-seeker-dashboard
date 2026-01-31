"""Visualization management for real-time progress tracking.

This module provides VisualizationManager for creating charts, dashboards,
and visual representations of progress tracking data.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
from uuid import UUID, uuid4

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
        self._stats = {
            "total_visualizations_created": 0,
            "total_dashboards_created": 0,
            "total_data_points_rendered": 0,
            "by_chart_type": defaultdict(int),
        }

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

    def get_stats(self) -> Dict[str, Any]:
        """Get visualization manager statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            **dict(self._stats),
            "total_widgets": len(self.dashboard_widgets),
        }


# Global visualization manager instance
visualization_manager = VisualizationManager()
