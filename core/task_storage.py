
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
TASKS_DIR = PROJECT_ROOT / "tasks"
TASKS_DIR.mkdir(exist_ok=True)


def create_task_file(task_text: str) -> Path:
    """Create a new task markdown file."""
    # Generate filename with timestamp
    timestamp = datetime.now()
    filename = timestamp.strftime("%Y-%m-%d_%H-%M-%S.md")
    file_path = TASKS_DIR / filename

    # Create task content
    content = f"""Voice Task
Timestamp: {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
Task:
{task_text}
Source:
Alexa-IFTTT
Status:
Pending
"""

    # Write to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Created task file: {file_path}")
    return file_path


if __name__ == "__main__":
    # Test function
    test_file = create_task_file("Test task from task_storage.py")
    print(f"Test task created at: {test_file}")
