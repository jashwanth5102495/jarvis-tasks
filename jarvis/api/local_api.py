
"""
Local API Module
================
Local REST API for JARVIS (uses FastAPI)
"""
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="JARVIS Local API", version="1.0.0")


class TaskRequest(BaseModel):
    user_input: str


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Any = None


@app.get("/")
async def root():
    return {"message": "JARVIS AI OS Local API", "status": "running"}


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    """Create a new task for JARVIS to execute."""
    # TODO: Integrate with core brain/planner/orchestrator
    return TaskResponse(task_id="1", status="accepted", result=None)


@app.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: str):
    """Get the status of a task."""
    # TODO: Implement
    return {"task_id": task_id, "status": "pending"}


@app.get("/api/v1/status")
async def get_status():
    """Get current JARVIS status."""
    return {"status": "idle", "components": ["brain", "planner", "orchestrator", "execution"]}

