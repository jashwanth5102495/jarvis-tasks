
import time
import logging
from pathlib import Path
from typing import Set
import sys
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directories to path
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from jarvis_server.agent.task_parser import (
    extract_task, summarize_task, generate_execution_plan
)
from jarvis_server.agent.executor import execute_task
from jarvis_server.core.git_manager import git_pull

# Get tasks directory
PROJECT_ROOT = Path(__file__).parent.parent
TASKS_DIR = PROJECT_ROOT / "tasks"
TASKS_DIR.mkdir(exist_ok=True)


class TaskWatcher:
    def __init__(self, check_interval: float = 2.0):
        self.check_interval = check_interval
        self.processed_tasks: Set[Path] = set()
        self.running = False
        self.watch_thread: threading.Thread | None = None
    
    def _scan_existing_tasks(self):
        """Scan tasks directory on startup to avoid processing old files."""
        for file in TASKS_DIR.glob("*.md"):
            self.processed_tasks.add(file)
        logger.info(f"Scanned {len(self.processed_tasks)} existing tasks (skipping)")
    
    def _check_for_new_tasks(self):
        """Check for new task files."""
        for file in TASKS_DIR.glob("*.md"):
            if file not in self.processed_tasks:
                logger.info(f"New task detected: {file.name}")
                self._process_task(file)
                self.processed_tasks.add(file)
    
    def _process_task(self, file_path: Path):
        """Process a new task file."""
        try:
            # Pull latest repo
            git_pull()
            
            # Extract and parse task
            task_text = extract_task(file_path)
            if not task_text:
                logger.warning("Empty task, skipping")
                return
            
            summarize_task(task_text)
            plan = generate_execution_plan(task_text)
            
            # Execute task (mock)
            execute_task(file_path, plan)
            
            logger.info(f"Task {file_path.name} processed successfully")
        except Exception as e:
            logger.error(f"Error processing task: {e}")
    
    def _watch_loop(self):
        """Main watch loop."""
        while self.running:
            self._check_for_new_tasks()
            time.sleep(self.check_interval)
    
    def start(self):
        """Start the task watcher."""
        if self.running:
            logger.warning("Task watcher already running")
            return
        
        self.running = True
        self._scan_existing_tasks()
        logger.info("Starting task watcher...")
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
    
    def stop(self):
        """Stop the task watcher."""
        self.running = False
        if self.watch_thread and self.watch_thread.is_alive():
            self.watch_thread.join(timeout=2.0)
        logger.info("Task watcher stopped")


if __name__ == "__main__":
    # Test the watcher
    watcher = TaskWatcher()
    watcher.start()
    
    # Keep alive for testing
    try:
        print("Task watcher running (Ctrl+C to stop)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping task watcher...")
        watcher.stop()
