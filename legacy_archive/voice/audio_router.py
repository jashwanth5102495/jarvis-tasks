
"""
audio_router.py
=============
Audio routing system for JARVIS. Handles microphone and speaker selection,
audio stream management, and simultaneous input/output.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AudioDevice:
    """Represents an audio device (microphone or speaker)."""
    id: str
    name: str
    type: str  # "input" or "output"
    is_default: bool = False
    sample_rate: int = 44100


class AudioRouter:
    """
    Manages audio devices and routing for JARVIS.
    Handles microphone/speaker selection and audio stream management.
    """

    def __init__(self):
        self._input_devices: List[AudioDevice] = []
        self._output_devices: List[AudioDevice] = []
        self._current_input: Optional[AudioDevice] = None
        self._current_output: Optional[AudioDevice] = None
        self._scan_devices()

    def _scan_devices(self) -> None:
        """Scan for available audio devices."""
        # Mock implementation for testing
        self._input_devices = [
            AudioDevice(id="mic1", name="Default Microphone", type="input", is_default=True),
            AudioDevice(id="mic2", name="USB Microphone", type="input")
        ]
        
        self._output_devices = [
            AudioDevice(id="speaker1", name="Default Speaker", type="output", is_default=True),
            AudioDevice(id="speaker2", name="Headphones", type="output")
        ]
        
        self._current_input = self._input_devices[0]
        self._current_output = self._output_devices[0]
        
        logger.info(f"Found {len(self._input_devices)} input devices, {len(self._output_devices)} output devices")

    def get_input_devices(self) -> List[AudioDevice]:
        """Get all available input (microphone) devices."""
        return self._input_devices.copy()

    def get_output_devices(self) -> List[AudioDevice]:
        """Get all available output (speaker) devices."""
        return self._output_devices.copy()

    def set_input_device(self, device_id: str) -> bool:
        """Set the active input device."""
        for device in self._input_devices:
            if device.id == device_id:
                self._current_input = device
                logger.info(f"Set input device to: {device.name}")
                return True
        
        logger.warning(f"Input device not found: {device_id}")
        return False

    def set_output_device(self, device_id: str) -> bool:
        """Set the active output device."""
        for device in self._output_devices:
            if device.id == device_id:
                self._current_output = device
                logger.info(f"Set output device to: {device.name}")
                return True
        
        logger.warning(f"Output device not found: {device_id}")
        return False

    def get_current_input(self) -> Optional[AudioDevice]:
        """Get the current input device."""
        return self._current_input

    def get_current_output(self) -> Optional[AudioDevice]:
        """Get the current output device."""
        return self._current_output

    def refresh_devices(self) -> None:
        """Refresh the list of available audio devices."""
        self._scan_devices()


# Module-level singleton
audio_router = AudioRouter()

