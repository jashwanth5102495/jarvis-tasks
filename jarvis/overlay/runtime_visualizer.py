
"""
state_visualizer.py
===================
State visualization logic for JARVIS runtime overlay.
Maps runtime states to visual properties.
"""

import logging
from typing import Tuple

from jarvis.runtime.runtime_state import RuntimeStatus
from jarvis.overlay.ui_theme_manager import ui_theme_manager, ThemeColors

logger = logging.getLogger(__name__)


class StateVisualizer:
    def __init__(self):
        self._colors: ThemeColors = ui_theme_manager.colors
        logger.info("State Visualizer initialized")

    def get_visual_properties(self, status: RuntimeStatus) -> dict:
        """Get visual properties for a given runtime status"""
        colors = ui_theme_manager.colors
        properties = {
            RuntimeStatus.IDLE: {
                "color": colors.active,
                "text": "🤖 Personal A.I Active",
                "animation": "breathing"
            },
            RuntimeStatus.PAUSED: {
                "color": colors.paused,
                "text": "🤖 Personal A.I Paused",
                "animation": "none"
            },
            RuntimeStatus.LISTENING: {
                "color": colors.listening,
                "text": "🤖 Listening...",
                "animation": "pulse"
            },
            RuntimeStatus.SPEAKING: {
                "color": colors.speaking,
                "text": "🤖 Speaking...",
                "animation": "pulse"
            },
            RuntimeStatus.EXECUTING: {
                "color": colors.executing,
                "text": "🤖 Executing Workflow...",
                "animation": "none"
            }
        }
        return properties.get(status, properties[RuntimeStatus.IDLE])

    def get_color_for_status(self, status: RuntimeStatus) -> str:
        """Get color hex code for a given status"""
        return self.get_visual_properties(status)["color"]

    def get_text_for_status(self, status: RuntimeStatus) -> str:
        """Get display text for a given status"""
        return self.get_visual_properties(status)["text"]


state_visualizer = StateVisualizer()

