
"""
background_scheduler.py
=======================
Schedules recurring tasks using the `schedule` library.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import schedule
except ImportError:
    logger.warning("schedule library not found. Install with: pip install schedule")
    schedule = None


class BackgroundScheduler:
    """
    Background task scheduler using `schedule` library.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._jobs: Dict[str, Any] = {}

    def start(self) -> None:
        if self._running:
            logger.warning("Scheduler is already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Started background scheduler")

    def stop(self) -> None:
        if not self._running:
            logger.warning("Scheduler is not running")
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Stopped background scheduler")

    def _run_loop(self) -> None:
        while self._running:
            if schedule:
                schedule.run_pending()
            time.sleep(1)

    def schedule_every(self, interval: int, unit: str, job: Callable, job_id: str) -> None:
        if not schedule:
            logger.error("schedule library not available")
            return

        if unit == "seconds":
            job_instance = schedule.every(interval).seconds.do(job)
        elif unit == "minutes":
            job_instance = schedule.every(interval).minutes.do(job)
        elif unit == "hours":
            job_instance = schedule.every(interval).hours.do(job)
        elif unit == "days":
            job_instance = schedule.every(interval).days.do(job)
        else:
            logger.error(f"Invalid time unit: {unit}")
            return

        self._jobs[job_id] = job_instance
        logger.info(f"Scheduled job {job_id} every {interval} {unit}")

    def cancel_job(self, job_id: str) -> None:
        if job_id in self._jobs:
            if schedule:
                schedule.cancel_job(self._jobs[job_id])
            del self._jobs[job_id]
            logger.info(f"Cancelled job {job_id}")


background_scheduler = BackgroundScheduler()
