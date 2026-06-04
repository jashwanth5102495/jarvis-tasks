
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

from jarvis_runtime.runtime_manager import main

if __name__ == "__main__":
    main()
