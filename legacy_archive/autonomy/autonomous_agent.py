
"""
autonomous_agent.py
====================
Base class for autonomous agents that run in the background.
"""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from autonomy.agent_registry import agent_registry

logger = logging.getLogger(__name__)


class AutonomousAgent(ABC):
    """
    Abstract base class for autonomous agents.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        description: str = "",
        interval_seconds: float = 60.0,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.description = description
        self.interval_seconds = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None

        agent_registry.register_agent(agent_id, agent_type, description)

    def start(self) -> None:
        """
        Start the agent in a background thread.
        """
        if self._running:
            logger.warning(f"Agent {self.agent_id} is already running")
            return
        self._running = True
        agent_registry.update_agent_status(self.agent_id, "running")
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Started agent: {self.agent_id}")

    def stop(self) -> None:
        """
        Stop the agent.
        """
        if not self._running:
            logger.warning(f"Agent {self.agent_id} is not running")
            return
        self._running = False
        agent_registry.update_agent_status(self.agent_id, "paused")
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info(f"Stopped agent: {self.agent_id}")

    def _run_loop(self) -> None:
        """
        Main loop that runs the agent's task periodically.
        """
        while self._running:
            try:
                self.execute()
            except Exception as e:
                logger.error(f"Agent {self.agent_id} error: {e}")
                agent_registry.update_agent_status(self.agent_id, "failed", {"error": str(e)})
            time.sleep(self.interval_seconds)

    @abstractmethod
    def execute(self) -> None:
        """
        Implement this method to define the agent's behavior.
        """
        pass
