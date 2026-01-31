"""Base chart component for progress visualization.

This module provides the base class for all chart components,
defining common interfaces and functionality.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class AnimationType(Enum):
    """Types of animations."""
    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    SCALE = "scale"
    BOUNCE = "bounce"
    PULSE = "pulse"


class ResponsiveBreakpoint(Enum):
    """Responsive design breakpoints."""
    MOBILE = "mobile"      # < 768px
    TABLET = "tablet"      # 768px - 1024px
    DESKTOP = "desktop"    # > 1024px
    LARGE = "large"        # > 1440px


class BaseChartComponent(ABC):
    """Base class for all chart components."""

    def __init__(
        self,
        component_id: str,
        width: int = 400,
        height: int = 300,
        responsive: bool = True,
        animation: AnimationType = AnimationType.FADE,
        animation_duration: int = 1000,
        theme: str = "default",
    ):
        """Initialize base chart component.

        Args:
            component_id: Unique component identifier
            width: Chart width in pixels
            height: Chart height in pixels
            responsive: Whether chart is responsive
            animation: Default animation type
            animation_duration: Animation duration in milliseconds
            theme: Chart theme name
        """
        self.component_id = component_id
        self.width = width
        self.height = height
        self.responsive = responsive
        self.animation = animation
        self.animation_duration = animation_duration
        self.theme = theme
        self.data: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.event_handlers: Dict[str, Callable] = {}
        self._is_initialized = False
        self._rendered_at: Optional[datetime] = None

    @abstractmethod
    async def render(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Render the chart component.

        Args:
            data: Chart data to render

        Returns:
            Rendered chart configuration
        """
        pass

    @abstractmethod
    async def update(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update the chart with new data.

        Args:
            new_data: New data for the chart

        Returns:
            Updated chart configuration
        """
        pass

    def set_data(self, data: List[Dict[str, Any]]):
        """Set chart data.

        Args:
            data: Chart data
        """
        self.data = data

    def get_data(self) -> List[Dict[str, Any]]:
        """Get current chart data.

        Returns:
            Current chart data
        """
        return self.data

    def set_metadata(self, metadata: Dict[str, Any]):
        """Set chart metadata.

        Args:
            metadata: Chart metadata
        """
        self.metadata = metadata

    def get_metadata(self) -> Dict[str, Any]:
        """Get chart metadata.

        Returns:
            Current chart metadata
        """
        return self.metadata

    def add_event_handler(self, event: str, handler: Callable):
        """Add event handler.

        Args:
            event: Event name
            handler: Event handler function
        """
        self.event_handlers[event] = handler

    def remove_event_handler(self, event: str):
        """Remove event handler.

        Args:
            event: Event name
        """
        if event in self.event_handlers:
            del self.event_handlers[event]

    async def handle_event(self, event: str, event_data: Any):
        """Handle chart event.

        Args:
            event: Event name
            event_data: Event data
        """
        if event in self.event_handlers:
            try:
                await self.event_handlers[event](event_data)
            except Exception as e:
                logger.error(f"Error handling event {event}: {e}")

    def get_config(self) -> Dict[str, Any]:
        """Get base chart configuration.

        Returns:
            Chart configuration dictionary
        """
        return {
            "component_id": self.component_id,
            "width": self.width,
            "height": self.height,
            "responsive": self.responsive,
            "animation": self.animation.value,
            "animation_duration": self.animation_duration,
            "theme": self.theme,
            "rendered_at": self._rendered_at.isoformat() if self._rendered_at else None,
        }

    def apply_responsive_config(self, breakpoint: ResponsiveBreakpoint):
        """Apply responsive configuration based on breakpoint.

        Args:
            breakpoint: Current screen breakpoint
        """
        if not self.responsive:
            return

        if breakpoint == ResponsiveBreakpoint.MOBILE:
            self.width = min(self.width, 320)
            self.height = min(self.height, 240)
        elif breakpoint == ResponsiveBreakpoint.TABLET:
            self.width = min(self.width, 600)
            self.height = min(self.height, 400)
        elif breakpoint == ResponsiveBreakpoint.DESKTOP:
            # Keep original dimensions
            pass
        elif breakpoint == ResponsiveBreakpoint.LARGE:
            # Scale up for large screens
            self.width = int(self.width * 1.2)
            self.height = int(self.height * 1.2)

    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate chart data.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        if not isinstance(data, list):
            return False

        # Override in subclasses for specific validation
        return len(data) >= 0

    def format_tooltip(self, data_point: Dict[str, Any]) -> str:
        """Format tooltip for data point.

        Args:
            data_point: Data point dictionary

        Returns:
            Formatted tooltip string
        """
        # Default tooltip formatting
        tooltip_parts = []
        for key, value in data_point.items():
            if key != "id":  # Skip internal ID
                tooltip_parts.append(f"{key}: {value}")

        return "\n".join(tooltip_parts)

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate basic statistics from data.

        Returns:
            Statistics dictionary
        """
        if not self.data:
            return {"count": 0}

        # Extract numeric values
        numeric_values = []
        for item in self.data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    numeric_values.append(value)

        if not numeric_values:
            return {"count": len(self.data)}

        return {
            "count": len(self.data),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "sum": sum(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
        }

    def export_data(self, format: str = "json") -> str:
        """Export chart data.

        Args:
            format: Export format (json, csv)

        Returns:
            Exported data as string
        """
        import json

        export_data = {
            "component_id": self.component_id,
            "type": self.__class__.__name__,
            "config": self.get_config(),
            "data": self.data,
            "metadata": self.metadata,
            "exported_at": datetime.utcnow().isoformat(),
        }

        if format == "json":
            return json.dumps(export_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def __repr__(self) -> str:
        """String representation.

        Returns:
            Component string representation
        """
        return (
            f"{self.__class__.__name__}("
            f"component_id='{self.component_id}', "
            f"width={self.width}, "
            f"height={self.height}"
            f")"
        )
