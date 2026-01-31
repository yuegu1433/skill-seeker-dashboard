"""Progress bar chart component.

This module provides ProgressBarComponent for displaying progress
with animations and custom styling.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseChartComponent, AnimationType

logger = logging.getLogger(__name__)


class ProgressBarComponent(BaseChartComponent):
    """Progress bar component for showing completion status."""

    def __init__(
        self,
        component_id: str,
        show_percentage: bool = True,
        show_label: bool = True,
        striped: bool = False,
        animated: bool = True,
        color_scheme: str = "blue",
        **kwargs,
    ):
        """Initialize progress bar component.

        Args:
            component_id: Component identifier
            show_percentage: Whether to show percentage
            show_label: Whether to show label
            striped: Whether to use striped pattern
            animated: Whether to use animation
            color_scheme: Color scheme name
            **kwargs: Additional base component arguments
        """
        super().__init__(component_id, **kwargs)
        self.show_percentage = show_percentage
        self.show_label = show_label
        self.striped = striped
        self.animated = animated
        self.color_scheme = color_scheme
        self.progress_value = 0.0
        self.label_text = ""

    async def render(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Render progress bar.

        Args:
            data: Progress data with 'progress' and 'label' fields

        Returns:
            Rendered progress bar configuration
        """
        if not self.validate_data(data):
            raise ValueError("Invalid progress bar data")

        # Extract progress value from data
        if data:
            progress_item = data[0]
            self.progress_value = float(progress_item.get("progress", 0))
            self.label_text = progress_item.get("label", "")

        # Ensure progress is between 0 and 100
        self.progress_value = max(0, min(100, self.progress_value))

        config = self.get_config()
        config.update({
            "type": "progress_bar",
            "progress": self.progress_value,
            "label": self.label_text,
            "show_percentage": self.show_percentage,
            "show_label": self.show_label,
            "striped": self.striped,
            "animated": self.animated,
            "color_scheme": self.color_scheme,
            "bar_style": self._get_bar_style(),
            "animation": self._get_animation_config(),
        })

        self._rendered_at = datetime.utcnow()
        self._is_initialized = True

        logger.debug(f"Rendered progress bar {self.component_id}: {self.progress_value}%")
        return config

    async def update(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update progress bar with new data.

        Args:
            new_data: New progress data

        Returns:
            Updated progress bar configuration
        """
        old_progress = self.progress_value

        # Render with new data
        config = await self.render(new_data)

        # Add transition metadata
        config["transition"] = {
            "from": old_progress,
            "to": self.progress_value,
            "duration": self.animation_duration,
            "easing": "ease-in-out",
        }

        return config

    def _get_bar_style(self) -> Dict[str, str]:
        """Get progress bar style configuration.

        Returns:
            Style configuration dictionary
        """
        color_map = {
            "blue": {"bg": "#3b82f6", "fg": "#ffffff"},
            "green": {"bg": "#10b981", "fg": "#ffffff"},
            "red": {"bg": "#ef4444", "fg": "#ffffff"},
            "yellow": {"bg": "#f59e0b", "fg": "#000000"},
            "purple": {"bg": "#8b5cf6", "fg": "#ffffff"},
            "gray": {"bg": "#6b7280", "fg": "#ffffff"},
        }

        colors = color_map.get(self.color_scheme, color_map["blue"])

        return {
            "background_color": colors["bg"],
            "text_color": colors["fg"],
            "height": "20px",
            "border_radius": "10px",
            "font_size": "14px",
            "font_weight": "bold",
        }

    def _get_animation_config(self) -> Dict[str, Any]:
        """Get animation configuration.

        Returns:
            Animation configuration
        """
        if not self.animated or self.animation == AnimationType.NONE:
            return {"enabled": False}

        animations = {
            AnimationType.FADE: {
                "type": "fadeIn",
                "duration": self.animation_duration,
                "delay": 0,
            },
            AnimationType.SLIDE: {
                "type": "slideInRight",
                "duration": self.animation_duration,
                "delay": 0,
            },
            AnimationType.SCALE: {
                "type": "scaleIn",
                "duration": self.animation_duration,
                "delay": 0,
            },
            AnimationType.BOUNCE: {
                "type": "bounceIn",
                "duration": self.animation_duration,
                "delay": 0,
            },
            AnimationType.PULSE: {
                "type": "pulse",
                "duration": self.animation_duration,
                "repeat": True,
            },
        }

        return animations.get(self.animation, {"enabled": False})

    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate progress bar data.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        if not super().validate_data(data):
            return False

        if not data:
            return True

        # Check if data has required fields
        first_item = data[0]
        if "progress" not in first_item:
            return False

        # Check if progress is numeric
        try:
            progress = float(first_item["progress"])
            return 0 <= progress <= 100
        except (ValueError, TypeError):
            return False

    def set_progress(self, value: float, label: str = ""):
        """Set progress value directly.

        Args:
            value: Progress value (0-100)
            label: Progress label
        """
        self.progress_value = max(0, min(100, value))
        self.label_text = label

    def get_progress(self) -> float:
        """Get current progress value.

        Returns:
            Current progress value
        """
        return self.progress_value

    def increment_progress(self, delta: float, label: str = ""):
        """Increment progress by delta.

        Args:
            delta: Amount to increment
            label: New label (optional)
        """
        self.set_progress(self.progress_value + delta, label)

    def is_complete(self) -> bool:
        """Check if progress is complete.

        Returns:
            True if progress is 100%
        """
        return self.progress_value >= 100

    def get_remaining(self) -> float:
        """Get remaining progress needed.

        Returns:
            Remaining progress (0-100)
        """
        return max(0, 100 - self.progress_value)

    def export_html(self) -> str:
        """Export progress bar as HTML.

        Returns:
            HTML string representation
        """
        style = self._get_bar_style()
        percentage_text = f"{self.progress_value:.1f}%" if self.show_percentage else ""

        html = f"""
        <div class="progress-bar-container" id="{self.component_id}">
            <div class="progress-bar-label">
                {self.label_text if self.show_label else ''}
                {percentage_text if self.show_percentage else ''}
            </div>
            <div class="progress-bar" style="
                background-color: #e5e7eb;
                border-radius: {style['border_radius']};
                height: {style['height']};
                width: 100%;
                overflow: hidden;
            ">
                <div class="progress-bar-fill" style="
                    background-color: {style['background_color']};
                    height: 100%;
                    width: {self.progress_value}%;
                    transition: width {self.animation_duration}ms ease;
                    {'background-image: linear-gradient(45deg, rgba(255,255,255,.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.15) 75%, transparent 75%, transparent);' if self.striped else ''}
                    {'background-size: 1rem 1rem;' if self.striped else ''}
                    {'animation: progress-bar-stripes 1s linear infinite;' if self.striped and self.animated else ''}
                "></div>
            </div>
        </div>
        """

        return html
