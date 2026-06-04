
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt


class SimpleOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Test Overlay")
        self.setGeometry(100, 100, 350, 70)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: red;")
        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = SimpleOverlay()
    sys.exit(app.exec())
