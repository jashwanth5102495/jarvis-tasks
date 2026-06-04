
import sys
from pathlib import Path
import uvicorn

sys.path.insert(0, str(Path(__file__).parent))

print("[JARVIS] Starting local server...")
print("[JARVIS] Listening on http://localhost:5000")
uvicorn.run("jarvis_server.app:app", host="0.0.0.0", port=5000, reload=False)
