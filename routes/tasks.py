
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path

# Add parent to path
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from jarvis_server.core.task_storage import create_task_file
from jarvis_server.core.git_manager import git_commit_push, ensure_repo_initialized

router = APIRouter(prefix="", tags=["tasks"])


class AddTaskRequest(BaseModel):
    task: str


@router.get("/health")
async def health_check():
    return {"status": "online"}


@router.post("/add_task")
async def add_task(request: AddTaskRequest):
    try:
        # Initialize repo if needed
        ensure_repo_initialized()
        
        # Create task file
        task_file = create_task_file(request.task)
        
        # Commit and push to git
        git_commit_push(task_file)
        
        return {
            "status": "success",
            "task": request.task,
            "file": str(task_file.name)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
