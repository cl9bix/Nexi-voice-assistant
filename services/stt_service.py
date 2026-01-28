import logging
import speech_recognition as sr
from config.settings import settings

logger = logging.getLogger(__name__)


class STTService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=settings.SAMPLE_RATE)
        self._calibrate()

    def _calibrate(self):
        logger.info("Калибровка микрофона...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.recognizer.energy_threshold = settings.ENERGY_THRESHOLD
            self.recognizer.dynamic_energy_threshold = True
        logger.info(f"Калибровка завершена. Порог: {self.recognizer.energy_threshold}")

    def listen(self, timeout: int = None, phrase_time_limit: int = None) -> str:
        timeout = timeout or settings.LISTEN_TIMEOUT
        phrase_time_limit = phrase_time_limit or settings.PHRASE_TIME_LIMIT

        with self.microphone as source:
            # logger.info("🎤 Слушаю...")
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            except sr.WaitTimeoutError:
                logger.debug("Таймаут ожидания речи")
                return None

        return self._recognize(audio)

    def _recognize(self, audio) -> str:
        try:
            text = self.recognizer.recognize_google(
                audio,
                language=settings.LANGUAGE
            )
            logger.info(f"Распознано: {text}")
            return text
        except sr.UnknownValueError:
            # logger.warning("Речь не распознана")
            pass
            return None
        except sr.RequestError as e:
            logger.error(f"Ошибка сервиса распознавания: {e}")
            return None

    def listen_continuous(self, callback, phrase_threshold: float = 0.5):
        logger.info("Запуск фонового прослушивания...")

        def wrapped_callback(recognizer, audio):
            text = self._recognize(audio)
            if text:
                callback(text)

        return self.recognizer.listen_in_background(
            self.microphone,
            wrapped_callback,
            phrase_threshold=phrase_threshold
        )