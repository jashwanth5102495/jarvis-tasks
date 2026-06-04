
import sys
from pathlib import Path
from fastapi import FastAPI
import uvicorn

# Make sure the parent directory (v1) is in path so we can import jarvis_server
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from jarvis_server.routes.tasks import router as tasks_router
from jarvis_server.agent.task_watcher import TaskWatcher


app = FastAPI(
    title="Jarvis Task Server",
    description="Local AI task server for voice-to-github workflows",
    version="2.0.0"
)


app.include_router(tasks_router)

# Initialize task watcher
task_watcher = TaskWatcher()


@app.on_event("startup")
async def startup_event():
    print("[JARVIS] Starting task watcher...")
    task_watcher.start()


@app.on_event("shutdown")
async def shutdown_event():
    print("[JARVIS] Stopping task watcher...")
    task_watcher.stop()


if __name__ == "__main__":
    print("[JARVIS] Starting task server...")
    print("[JARVIS] Listening on http://localhost:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)
