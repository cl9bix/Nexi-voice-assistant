import logging
import threading
import queue
import time
import pyttsx3
from pathlib import Path
from config.settings import settings
from config.prompts import VOICE_ASSISTANT_NAME, OWNER_NAME

logger = logging.getLogger(__name__)


class LocalTTSService:
    def __init__(self):
        self.engine = None
        self.queue = queue.Queue()
        self.speaking = False
        self._stop_event = threading.Event()
        self._init_engine()
        self._start_worker()

    def _init_engine(self):
        """Ініціалізація локального TTS движка"""
        try:
            self.engine = pyttsx3.init()
            self._configure_voice()
            self.engine.setProperty('rate', 180)  # Швидкість мови
            self.engine.setProperty('volume', 0.9)  # Гучність

            # Персоналізація для Юрія
            self.engine.setProperty('pitch', 105)  # Тональність голосу

            logger.info(f"Local TTS инициализирован для {VOICE_ASSISTANT_NAME}")

        except Exception as e:
            logger.error(f"Ошибка инициализации локального TTS: {e}")
            # Fallback на стандартний голос
            self.engine = pyttsx3.init()

    def _configure_voice(self):
        """Налаштування голосу для русської мови"""
        voices = self.engine.getProperty('voices')

        # Шукаємо русский або український голос
        target_voice = None
        for voice in voices:
            voice_name = voice.name.lower()
            if any(lang in voice_name for lang in ['russian', 'русский', 'ukrainian', 'украинский']):
                target_voice = voice.id
                logger.info(f"Найден русский/украинский голос: {voice.name}")
                break

        # Якщо не знайшли - шукаємо англійський але з хорошою вимовою
        if not target_voice:
            for voice in voices:
                if 'english' in voice.name.lower() or 'en' in voice.name.lower():
                    target_voice = voice.id
                    logger.info(f"Используем английский голос: {voice.name}")
                    break

        # Встановлюємо знайдений голос
        if target_voice:
            self.engine.setProperty('voice', target_voice)
        else:
            logger.warning("Не найден подходящий голос, используется стандартный")

    def _init_engine(self):
        """Ініціалізація локального TTS движка"""
        try:
            self.engine = pyttsx3.init()
            self._configure_voice()
            self.engine.setProperty('rate', 180)  # Швидкість мови
            self.engine.setProperty('volume', 0.9)  # Гучність

            # ПРИБИРАЄМО ЦЮ ЛІНІЮ:
            # self.engine.setProperty('pitch', 105)  # <--- ПРИБРАТИ!

            logger.info(f"Local TTS инициализирован для {VOICE_ASSISTANT_NAME}")

        except Exception as e:
            logger.error(f"Ошибка инициализации локального TTS: {e}")
            # Fallback на стандартний голос
            self.engine = pyttsx3.init()

    def _start_worker(self):
        """Запуск робочого потоку для озвучення"""

        def worker():
            while not self._stop_event.is_set():
                try:
                    text = self.queue.get(timeout=0.5)
                    if text is None:
                        break
                    self._speak(text)
                    self.queue.task_done()
                except queue.Empty:
                    continue

        self.thread = threading.Thread(target=worker, daemon=True)
        self.thread.start()

    def _speak(self, text: str):
        """Озвучення тексту локальним движком з емоційною інтонацією"""
        if not self.engine:
            return

        try:
            self.speaking = True

            # Персоналізація тексту для Юрія
            personalized_text = self._personalize_text(text)

            logger.info(f"🔊 Local TTS: {personalized_text[:100]}...")

            # Емоційна інтонація через швидкість:
            if "привет" in personalized_text.lower() or "доброе" in personalized_text.lower():
                # Вітальна інтонація - трохи швидше та жвавіше
                self.engine.setProperty('rate', 190)
            elif "спасибо" in personalized_text.lower() or "отлично" in personalized_text.lower():
                # Позитивна інтонація - середня швидкість
                self.engine.setProperty('rate', 175)
            elif "ошибка" in personalized_text.lower() or "проблема" in personalized_text.lower():
                # Повільніше для серйозних повідомлень
                self.engine.setProperty('rate', 160)
            else:
                # Нормальна швидкість
                self.engine.setProperty('rate', 180)

            # Додаємо паузи для кращого сприйняття
            if "!" in personalized_text:
                personalized_text = personalized_text.replace("!", "... ")
            if "?" in personalized_text:
                personalized_text = personalized_text.replace("?", "... ")

            self.engine.say(personalized_text)
            self.engine.runAndWait()

            self.speaking = False

        except Exception as e:
            logger.error(f"Ошибка озвучивания: {e}")
            self.speaking = False

    def _personalize_text(self, text: str) -> str:
        """Персоналізація тексту для Юрія з емоціями"""
        # Замінюємо звернення
        text = text.replace("пользователь", OWNER_NAME)
        text = text.replace("владелец", OWNER_NAME)
        text = text.replace("шеф", OWNER_NAME)

        # Емоційні вставки
        if "привет" in text.lower():
            text = f"Привет, {OWNER_NAME}! Рад тебя слышать! {text}"
        elif "спасибо" in text.lower():
            text = f"Пожалуйста, {OWNER_NAME}! Всегда рад помочь! {text}"
        elif "как дела" in text.lower():
            text = f"У меня все отлично, {OWNER_NAME}! Надеюсь, у тебя тоже! {text}"
        elif "венгрия" in text.lower():
            text = f"Как тебе Веспрем, {OWNER_NAME}? {text}"
        elif "backend" in text.lower() or "code" in text.lower():
            text = f"Как backend разработчик, ты знаешь, {OWNER_NAME}, {text}"

        # Технічна вимова
        tech_replacements = {
            "API": "А Пи Ай",
            "FastAPI": "Фаст А Пи Ай",
            "Django": "Джанго",
            "backend": "бекенд",
            "frontend": "фронтенд",
            "GPT": "Ги Пи Ти",
            "AI": "Ай Ай",
            "VS Code": "Ви Ес Код",
            "JSON": "Джейсон",
            "SQL": "Эс Кью Эл",
            "Python": "Пайтон",
            "JavaScript": "ДжаваСкрипт",
            "Linux": "Линукс",
            "Windows": "Виндовс",
            "Jarvis": "Джарвис",
            "TTS": "Ти Ти Эс",
            "STT": "Эс Ти Ти"
        }

        for eng, rus in tech_replacements.items():
            text = text.replace(eng, rus)

        return text

    def speak(self, text: str, priority: bool = False) -> bool:
        """Додати текст в чергу на озвучення"""
        if not text:
            return False

        if priority:
            # Для пріоритетних повідомлень очищаємо чергу
            self.clear_queue()

        self.queue.put(text)
        return True

    def speak_immediately(self, text: str) -> bool:
        """Блокуюче озвучення (чекає закінчення)"""
        if not text:
            return False

        try:
            personalized_text = self._personalize_text(text)
            logger.info(f"🔊 Local TTS (immediate): {personalized_text[:100]}...")

            self.speaking = True
            self.engine.say(personalized_text)
            self.engine.runAndWait()
            self.speaking = False

            return True

        except Exception as e:
            logger.error(f"Ошибка немедленного озвучивания: {e}")
            self.speaking = False
            return False

    def stop(self):
        """Зупинка озвучення та очищення черги"""
        try:
            # Зупиняємо поточне мовлення
            if self.engine:
                self.engine.stop()

            # Очищаємо чергу
            self.clear_queue()

            # Сигнал зупинки
            self._stop_event.set()
            self.queue.put(None)

            # Чекаємо завершення потоку
            if self.thread:
                self.thread.join(timeout=2)

            self.speaking = False
            logger.info("Local TTS остановлен")

        except Exception as e:
            logger.error(f"Ошибка остановки TTS: {e}")

    def clear_queue(self):
        """Очищення черги озвучення"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    def is_speaking(self) -> bool:
        """Перевірка чи зараз говорить"""
        return self.speaking or not self.queue.empty()

    def set_voice(self, voice_id: str):
        """Зміна голосу"""
        try:
            if self.engine and voice_id:
                self.engine.setProperty('voice', voice_id)
                logger.info(f"Голос изменен на: {voice_id}")
        except Exception as e:
            logger.error(f"Ошибка смены голоса: {e}")

    def set_speed(self, speed: int):
        """Зміна швидкості мови"""
        try:
            if self.engine:
                self.engine.setProperty('rate', speed)
                logger.info(f"Скорость речи изменена на: {speed}")
        except Exception as e:
            logger.error(f"Ошибка изменения скорости: {e}")


# Адаптер для сумісності
class TTSService(LocalTTSService):
    """Адаптер для сумісності - просто наслідуємо LocalTTSService"""
    pass