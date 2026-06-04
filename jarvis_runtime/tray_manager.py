
import os
import threading
import webbrowser
from pathlib import Path

from jarvis_runtime.logger import get_logger
from jarvis_runtime.runtime_state import get_state, set_state, RuntimeState
from jarvis_runtime.server_launcher import start_fastapi_server, stop_fastapi_server, restart_fastapi_server


logger = get_logger()
tray_stop_event = threading.Event()

tray_available = True
try:
    from PIL import Image
    import pystray
    from pystray import MenuItem as item
except ImportError as e:
    logger.warning(f"System tray dependencies not found: {e}")
    tray_available = False


if tray_available:
    def get_jarvis_icon():
        icons_dir = Path(__file__).parent / "icons"
        icon_path = icons_dir / "jarvis.ico"
        
        if icon_path.exists():
            return Image.open(icon_path)
        
        # Fallback to a simple colored icon
        img = Image.new('RGB', (64, 64), color='blue')
        return img


    def open_dashboard():
        webbrowser.open("http://localhost:5000")


    def restart_jarvis():
        logger.info("Tray: Restarting Jarvis...")
        restart_fastapi_server()


    def view_logs():
        log_dir = Path(__file__).parent.parent / "logs"
        log_file = log_dir / "jarvis_runtime.log"
        if log_file.exists():
            os.startfile(str(log_file))
        else:
            webbrowser.open(str(log_dir))


    def pause_runtime():
        logger.info("Tray: Pausing runtime")
        set_state(RuntimeState.PAUSED)


    def resume_runtime():
        logger.info("Tray: Resuming runtime")
        start_fastapi_server()


    def exit_application():
        logger.info("Tray: Exiting application...")
        set_state(RuntimeState.SHUTTING_DOWN)
        stop_fastapi_server()
        tray_stop_event.set()
        if tray_icon:
            tray_icon.stop()


    def create_tray_menu():
        return pystray.Menu(
            item("Open Dashboard", open_dashboard),
            item("Restart Jarvis", restart_jarvis),
            item("View Logs", view_logs),
            pystray.Menu.SEPARATOR,
            item("Pause Runtime", pause_runtime, enabled=lambda item: get_state() != RuntimeState.PAUSED),
            item("Resume Runtime", resume_runtime, enabled=lambda item: get_state() == RuntimeState.PAUSED),
            pystray.Menu.SEPARATOR,
            item("Exit", exit_application)
        )


    def start_tray():
        global tray_icon
        tray_icon = pystray.Icon(
            name="Jarvis",
            icon=get_jarvis_icon(),
            title="Jarvis AI Runtime",
            menu=create_tray_menu()
        )
        tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
        tray_thread.start()
        logger.info("System tray started")
else:
    def start_tray():
        logger.warning("System tray not available - running without tray")
        logger.info("Press Ctrl+C to stop Jarvis Runtime Manager")

