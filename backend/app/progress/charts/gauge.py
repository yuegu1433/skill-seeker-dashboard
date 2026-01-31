"""Gauge chart component.

This module provides GaugeComponent for displaying
single metric values with circular gauges.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseChartComponent, AnimationType

logger = logging.getLogger(__name__)


class GaugeComponent(BaseChartComponent):
    """Gauge component for displaying single metric values."""

    def __init__(
        self,
        component_id: str,
        min_value: float = 0,
        max_value: float = 100,
        unit: str = "",
        show_min_max: bool = True,
        show_value: bool = True,
        color_scheme: str = "default",
        gauge_type: str = "semicircle",
        **kwargs,
    ):
        """Initialize gauge component.

        Args:
            component_id: Component identifier
            min_value: Minimum gauge value
            max_value: Maximum gauge value
            unit: Unit label
            show_min_max: Whether to show min/max labels
            show_value: Whether to show current value
            color_scheme: Color scheme name
            gauge_type: Gauge type (semicircle, fullcircle, arc)
            **kwargs: Additional base component arguments
        """
        super().__init__(component_id, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.show_min_max = show_min_max
        self.show_value = show_value
        self.color_scheme = color_scheme
        self.gauge_type = gauge_type
        self.current_value = min_value
        self.label = ""

    async def render(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Render gauge component.

        Args:
            data: Gauge data with 'value' and optional 'label'

        Returns:
            Rendered gauge configuration
        """
        # Extract value and label from data
        if data:
            first_item = data[0]
            self.current_value = float(first_item.get("value", self.min_value))
            self.label = first_item.get("label", "")

        # Ensure value is within range
        self.current_value = max(self.min_value, min(self.max_value, self.current_value))

        config = self.get_config()
        config.update({
            "type": "gauge",
            "value": self.current_value,
            "label": self.label,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "unit": self.unit,
            "show_min_max": self.show_min_max,
            "show_value": self.show_value,
            "color_scheme": self.color_scheme,
            "gauge_type": self.gauge_type,
            "gauge_style": self._get_gauge_style(),
            "color_ranges": self._get_color_ranges(),
            "animation": self._get_animation_config(),
        })

        self._rendered_at = datetime.utcnow()
        self._is_initialized = True

        logger.debug(f"Rendered gauge {self.component_id}: {self.current_value}")
        return config

    async def update(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update gauge with new data.

        Args:
            new_data: New gauge data

        Returns:
            Updated gauge configuration
        """
        old_value = self.current_value

        # Render with new data
        config = await self.render(new_data)

        # Add transition metadata
        config["transition"] = {
            "type": "value_update",
            "from": old_value,
            "to": self.current_value,
            "duration": self.animation_duration,
            "easing": "easeInOutCubic",
        }

        return config

    def _get_gauge_style(self) -> Dict[str, Any]:
        """Get gauge style configuration.

        Returns:
            Style configuration dictionary
        """
        styles = {
            "default": {
                "thickness": 20,
                "background_color": "#e5e7eb",
                "border_radius": 10,
                "font_size": "24px",
                "font_weight": "bold",
            },
            "thick": {
                "thickness": 30,
                "background_color": "#d1d5db",
                "border_radius": 15,
                "font_size": "28px",
                "font_weight": "bold",
            },
            "thin": {
                "thickness": 10,
                "background_color": "#f3f4f6",
                "border_radius": 5,
                "font_size": "20px",
                "font_weight": "normal",
            },
        }

        return styles.get(self.color_scheme, styles["default"])

    def _get_color_ranges(self) -> List[Dict[str, Any]]:
        """Get color ranges for gauge.

        Returns:
            List of color range configurations
        """
        range_configs = {
            "default": [
                {"min": 0, "max": 50, "color": "#ef4444"},    # Red
                {"min": 50, "max": 80, "color": "#f59e0b"},   # Yellow
                {"min": 80, "max": 100, "color": "#10b981"},   # Green
            ],
            "performance": [
                {"min": 0, "max": 30, "color": "#ef4444"},    # Red
                {"min": 30, "max": 70, "color": "#f59e0b"},   # Yellow
                {"min": 70, "max": 100, "color": "#10b981"},   # Green
            ],
            "temperature": [
                {"min": 0, "max": 33, "color": "#3b82f6"},   # Blue
                {"min": 33, "max": 66, "color": "#10b981"},   # Green
                {"min": 66, "max": 100, "color": "#ef4444"},  # Red
            ],
            "single": [
                {"min": 0, "max": 100, "color": "#3b82f6"},   # Single color
            ],
        }

        return range_configs.get(self.color_scheme, range_configs["default"])

    def _get_animation_config(self) -> Dict[str, Any]:
        """Get animation configuration.

        Returns:
            Animation configuration
        """
        if self.animation == AnimationType.NONE:
            return {"enabled": False}

        animations = {
            AnimationType.FADE: {
                "type": "fadeIn",
                "duration": self.animation_duration,
            },
            AnimationType.SCALE: {
                "type": "scaleIn",
                "duration": self.animation_duration,
            },
            AnimationType.PULSE: {
                "type": "pulse",
                "duration": self.animation_duration,
                "repeat": True,
            },
        }

        return animations.get(self.animation, {"enabled": False})

    def set_value(self, value: float, label: str = ""):
        """Set gauge value directly.

        Args:
            value: Gauge value
            label: Gauge label
        """
        self.current_value = max(self.min_value, min(self.max_value, value))
        if label:
            self.label = label

    def get_value(self) -> float:
        """Get current gauge value.

        Returns:
            Current value
        """
        return self.current_value

    def get_percentage(self) -> float:
        """Get current value as percentage.

        Returns:
            Percentage value (0-100)
        """
        range_size = self.max_value - self.min_value
        if range_size == 0:
            return 0

        return ((self.current_value - self.min_value) / range_size) * 100

    def get_color(self) -> str:
        """Get color for current value.

        Returns:
            Color string
        """
        percentage = self.get_percentage()

        for color_range in self._get_color_ranges():
            if color_range["min"] <= percentage <= color_range["max"]:
                return color_range["color"]

        return "#6b7280"  # Default gray

    def increment(self, delta: float):
        """Increment gauge value.

        Args:
            delta: Amount to increment
        """
        self.set_value(self.current_value + delta)

    def decrement(self, delta: float):
        """Decrement gauge value.

        Args:
            delta: Amount to decrement
        """
        self.set_value(self.current_value - delta)

    def is_at_max(self) -> bool:
        """Check if gauge is at maximum value.

        Returns:
            True if at maximum
        """
        return self.current_value >= self.max_value

    def is_at_min(self) -> bool:
        """Check if gauge is at minimum value.

        Returns:
            True if at minimum
        """
        return self.current_value <= self.min_value

    def get_remaining(self) -> float:
        """Get remaining value to reach maximum.

        Returns:
            Remaining value
        """
        return max(0, self.max_value - self.current_value)

    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate gauge data.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        if not super().validate_data(data):
            return False

        if not data:
            return True

        # Check if data has value field
        first_item = data[0]
        if "value" not in first_item:
            return False

        # Check if value is numeric
        try:
            value = float(first_item["value"])
            return self.min_value <= value <= self.max_value
        except (ValueError, TypeError):
            return False

    def export_html(self) -> str:
        """Export gauge as HTML.

        Returns:
            HTML string representation
        """
        percentage = self.get_percentage()
        color = self.get_color()
        style = self._get_gauge_style()

        html = f"""
        <div class="gauge-container" id="{self.component_id}">
            <div class="gauge-label">{self.label}</div>
            <div class="gauge-value" style="
                font-size: {style['font_size']};
                font-weight: {style['font_weight']};
                color: {color};
            ">
                {self.current_value:.1f}{self.unit}
            </div>
            <svg class="gauge-svg" width="200" height="120" viewBox="0 0 200 120">
                <path d="M 20 100 A 80 80 0 0 1 180 100"
                      fill="none"
                      stroke="{style['background_color']}"
                      stroke-width="{style['thickness']}"
                      stroke-linecap="round" />
                <path d="M 20 100 A 80 80 0 0 1 180 100"
                      fill="none"
                      stroke="{color}"
                      stroke-width="{style['thickness']}"
                      stroke-linecap="round"
                      stroke-dasharray="{percentage * 2.51} 251"
                      style="transition: stroke-dasharray {self.animation_duration}ms ease;" />
            </svg>
            {f'<div class="gauge-min">{self.min_value}</div>' if self.show_min_max else ''}
            {f'<div class="gauge-max">{self.max_value}</div>' if self.show_min_max else ''}
        </div>
        """

        return html
