
import subprocess
from pathlib import Path
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent


def run_command(command: list[str], cwd: Optional[Path] = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Command succeeded: {' '.join(command)}")
        logger.debug(f"Output: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}")
        logger.error(f"Error: {e.stderr}")
        return False, e.stderr


def ensure_repo_initialized() -> bool:
    """Ensure git repo is initialized."""
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        logger.info("Initializing git repository...")
        success, _ = run_command(["git", "init"])
        if success:
            # Create initial .gitignore
            gitignore = PROJECT_ROOT / ".gitignore"
            if not gitignore.exists():
                with open(gitignore, "w") as f:
                    f.write("__pycache__/\n*.pyc\n*.log\nvenv/\n.env\n")
                run_command(["git", "add", ".gitignore"])
                run_command(["git", "config", "user.email", "jarvis@local"])
                run_command(["git", "config", "user.name", "Jarvis AI"])
                run_command(["git", "commit", "-m", "Initial commit"])
        return success
    return True


def git_pull() -> bool:
    """Pull latest from remote repo."""
    logger.info("Pulling latest from git...")
    success, _ = run_command(["git", "pull"])
    return success


def git_commit_push(file_path: Path) -> bool:
    """Commit and push a file."""
    try:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        logger.info(f"Committing and pushing: {relative_path}")
        
        # Stage file
        add_success, _ = run_command(["git", "add", str(relative_path)])
        if not add_success:
            return False
        
        # Commit
        commit_success, _ = run_command([
            "git", "commit", "-m", "New voice task added"
        ])
        if not commit_success:
            return False
        
        # Push (if remote exists)
        # Check if remote is configured
        remote_success, _ = run_command(["git", "remote", "-v"])
        if remote_success:
            push_success, _ = run_command(["git", "push"])
            if not push_success:
                logger.warning("Push failed, but commit succeeded locally.")
        
        return True
    except ValueError as e:
        logger.error(f"File not in project root: {e}")
        return False


if __name__ == "__main__":
    print("Testing git_manager...")
    ensure_repo_initialized()
