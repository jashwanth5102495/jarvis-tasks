
import sys
import logging
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent / "logs" / "runtime_ui_logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "test.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import Qt first!
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Overlay")
        self.setFixedSize(400, 100)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: red; color: white; font-size: 20px;")
        
        layout = QVBoxLayout()
        self.label = QLabel("Testing Overlay!")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.show()
        self.raise_()
        self.activateWindow()
        logger.info("Test window shown!")

def main():
    app = QApplication(sys.argv)
    test_window = TestWindow()
    
    # Test TTS
    from voice.text_to_speech import text_to_speech
    QTimer.singleShot(1000, lambda: text_to_speech.speak("Hello, this is a test of the text to speech system!"))
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
