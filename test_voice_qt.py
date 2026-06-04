
"""
Test voice playing inside a Qt event loop!
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer


def speak_in_qt():
    import pyttsx3
    logging.info("Initializing pyttsx3 in Qt")
    engine = pyttsx3.init(driverName='sapi5')
    voices = engine.getProperty('voices')
    for v in voices:
        if "Microsoft David" in v.name:
            engine.setProperty('voice', v.id)
    engine.setProperty('volume', 1.0)
    engine.setProperty('rate', 150)
    
    logging.info("Starting to speak now (in Qt event loop)")
    try:
        engine.say("This is a test! JARVIS voice inside a Qt event loop!")
        logging.info("Calling engine.runAndWait()")
        engine.runAndWait()
        logging.info("DONE SPEAKING!")
        # Quit the app after a second
        QTimer.singleShot(1000, QApplication.quit)
    except Exception as e:
        logging.error(f"ERROR SPEAKING: {e}", exc_info=True)
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    logging.info("Qt app created")
    QTimer.singleShot(500, speak_in_qt)
    app.exec()
