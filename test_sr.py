
import speech_recognition as sr
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_speech_recognition():
    logger.info("Testing Speech Recognition...")
    r = sr.Recognizer()
    r.energy_threshold = 200
    r.dynamic_energy_threshold = False
    try:
        with sr.Microphone() as source:
            logger.info("Say something!")
            audio = r.listen(source, phrase_time_limit=3)
            logger.info("Got audio!")
        text = r.recognize_google(audio).lower()
        logger.info(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        logger.error("Could not understand audio")
    except sr.RequestError as e:
        logger.error(f"Could not request results: {e}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    test_speech_recognition()
