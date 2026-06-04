
"""
JARVIS AI Operating System
==========================
Main entry point for the JARVIS AI OS
"""
import sys
import logging
import threading
import asyncio
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent.parent / "logs" / "jarvis"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / f"jarvis_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_overlay():
    """Run the PyQt6 overlay UI in the main thread."""
    from PyQt6.QtWidgets import QApplication
    from jarvis.overlay.overlay_manager import overlay_manager
    from jarvis.overlay.tray_manager import tray_manager

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_manager.initialize()
    tray_manager.start()

    overlay_manager.initialize()
    overlay_manager.start_in_main_thread()

    sys.exit(app.exec())


def run_runtime():
    """Run the JARVIS runtime in a background thread."""
    from jarvis.runtime.runtime_manager import runtime_manager
    from jarvis.runtime.hotkey_manager import hotkey_manager
    from jarvis.voice.voice_manager import voice_manager

    runtime_manager.initialize(enable_startup=True)
    hotkey_manager.initialize()
    hotkey_manager.start()
    voice_manager.initialize()
    voice_manager.start()

    try:
        runtime_manager.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received - shutting down")
        runtime_manager.shutdown()


def main():
    logger.info("=" * 70)
    logger.info("JARVIS AI Operating System")
    logger.info("=" * 70)

    # Run overlay in main thread (required for Qt)
    # and runtime in a background thread
    runtime_thread = threading.Thread(target=run_runtime, daemon=True, name="JARVIS-Runtime")
    runtime_thread.start()

    run_overlay()


if __name__ == "__main__":
    main()

