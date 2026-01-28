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
            logger.info("🎯 Начало инициализации TTS движка...")
            self.engine = pyttsx3.init()
            logger.info("✅ Pyttsx3 инициализирован")

            self._configure_voice()

            # Параметри з логуванням
            self.engine.setProperty('rate', settings.TTS_VOICE_SPEED)
            logger.info(f"📢 Скорость установлена: {settings.TTS_VOICE_SPEED}")

            self.engine.setProperty('volume', 1.0)  # МАКСИМАЛЬНА громкость!
            logger.info("🔊 Громкость установлена: 100%")

            logger.info(f"✅ TTS движок готов для {VOICE_ASSISTANT_NAME}")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации TTS: {e}")
            self.engine = pyttsx3.init()

    def _configure_voice(self):
        """Налаштування голосу з логуванням"""
        try:
            voices = self.engine.getProperty('voices')
            logger.info(f"📢 Найдено голосов: {len(voices)}")

            for i, voice in enumerate(voices):
                logger.info(f"  Голос {i}: {voice.name}")

            # Вибираємо перший доступний
            if voices:
                self.engine.setProperty('voice', voices[0].id)
                logger.info(f"✅ Использую голос: {voices[0].name}")
            else:
                logger.warning("⚠️ Нет доступных голосов")

        except Exception as e:
            logger.error(f"❌ Ошибка конфигурации голоса: {e}")

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
        """Озвучення з максимальним логуванням"""
        if not self.engine:
            logger.error("❌ Движок TTS не инициализирован!")
            return

        try:
            self.speaking = True
            logger.info(f"🔊 Начинаю озвучивание: {text[:50]}...")

            # Персоналізація
            personalized_text = self._personalize_text(text)
            logger.info(f"📝 Персонализированный текст: {personalized_text[:50]}...")

            # Виводимо властивості перед озвученням
            rate = self.engine.getProperty('rate')
            volume = self.engine.getProperty('volume')
            logger.info(f"📊 Текущие настройки: rate={rate}, volume={volume}")

            self.engine.say(personalized_text)
            logger.info("📢 Отправляю текст в движок...")

            self.engine.runAndWait()
            logger.info("✅ Озвучивание завершено")

            self.speaking = False

        except Exception as e:
            logger.error(f"❌ Ошибка озвучивания: {e}")
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
        """Блокуюче озвучення з логами"""
        try:
            logger.info(f"🔊 Немедленное озвучивание: {text}")

            personalized_text = self._personalize_text(text)

            self.speaking = True
            self.engine.say(personalized_text)
            logger.info("📢 Запуск runAndWait...")
            self.engine.runAndWait()
            logger.info("✅ Немедленное озвучивание завершено")
            self.speaking = False

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка немедленного озвучивания: {e}")
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
            logger.info("✅ Local TTS остановлен")

        except Exception as e:
            logger.error(f"❌ Ошибка остановки TTS: {e}")

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
                logger.info(f"✅ Голос изменен на: {voice_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка смены голоса: {e}")

    def set_speed(self, speed: int):
        """Зміна швидкості мови"""
        try:
            if self.engine:
                self.engine.setProperty('rate', speed)
                logger.info(f"✅ Скорость речи изменена на: {speed}")
        except Exception as e:
            logger.error(f"❌ Ошибка изменения скорости: {e}")


# Адаптер для сумісності
class TTSService(LocalTTSService):
    pass