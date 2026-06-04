
"""
setup_autostart.py
==================
Simple script to enable or disable JARVIS auto-start on Windows login.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)

from runtime.startup_manager import startup_manager

def main():
    print("=" * 60)
    print("JARVIS Auto-Start Setup")
    print("=" * 60)
    print()

    if len(sys.argv) == 1:
        print("Usage:")
        print("  python setup_autostart.py enable   - Enable auto-start on login")
        print("  python setup_autostart.py disable  - Disable auto-start")
        print()
        return

    command = sys.argv[1].lower()
    if command == "enable":
        success = startup_manager.enable_startup()
        if success:
            print("[OK] JARVIS auto-start has been enabled!")
            print("   JARVIS will now start automatically when you log into Windows.")
        else:
            print("[FAILED] Failed to enable auto-start!")
    elif command == "disable":
        success = startup_manager.disable_startup()
        if success:
            print("[OK] JARVIS auto-start has been disabled!")
        else:
            print("[OK] JARVIS auto-start was not enabled.")
    else:
        print(f"Unknown command: {command}")
        print("Use 'enable' or 'disable'.")


if __name__ == "__main__":
    main()

