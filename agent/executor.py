
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_task(file_path: Path, plan: list[str]):
    """Mock task executor."""
    logger.info("="*50)
    logger.info(f"Starting execution of task: {file_path.name}")
    logger.info("="*50)
    
    for step in plan:
        logger.info(f"Executing step: {step}")
    
    logger.info("="*50)
    logger.info("Task execution completed (mock)")
    logger.info("="*50)


if __name__ == "__main__":
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
        f.write("Test task")
        test_path = Path(f.name)
    
    execute_task(test_path, ["Step 1", "Step 2"])
    test_path.unlink()
