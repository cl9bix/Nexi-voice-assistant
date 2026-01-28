import json
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from config.settings import settings
from config.prompts import (
    SYSTEM_PROMPT, CONFIRMATION_PROMPT,
    VOICE_ASSISTANT_NAME, OWNER_NAME, GREETINGS
)
from core.function_registry import FunctionRegistry
from core.context_manager import ContextManager
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_service import LLMService
from utils.safety import SafetyChecker

logger = logging.getLogger(__name__)


class VoiceAssistant:
    def __init__(self):
        self.registry = FunctionRegistry()
        self.context = ContextManager()
        self.stt = STTService()
        self.tts = TTSService()
        self.llm = LLMService()

        self._setup_context()
        self.running = False
        self.awaiting_confirmation = False
        self.pending_function = None

    def _setup_context(self):
        schema = self.registry.get_schema_json()
        prompt = f"{SYSTEM_PROMPT}\n\nДоступные функции:\n{schema}"
        self.context.set_system_prompt(prompt)
        logger.info(f"{VOICE_ASSISTANT_NAME} контекст инициализирован для {OWNER_NAME}")

    def _get_greeting(self) -> str:
        """Персонализированное приветствие на основе времени суток"""
        current_hour = datetime.now().hour

        if 6 <= current_hour < 12:
            return GREETINGS["morning"]
        elif 12 <= current_hour < 18:
            return GREETINGS["day"]
        elif 18 <= current_hour < 23:
            return GREETINGS["evening"]
        else:
            return GREETINGS["night"]

    def process_text(self, text: str, skip_tts: bool = False) -> str:
        logger.info(f"[{OWNER_NAME}] Запрос: {text}")

        # Проверяем ожидание подтверждения
        if self.awaiting_confirmation:
            return self._handle_confirmation(text)

        # Персонализируем запрос
        personalized_text = f"Юрий говорит: {text}"
        self.context.add_user_message(personalized_text)

        messages = self.context.get_messages_for_llm()
        functions = self.registry.get_schema()

        response = self.llm.get_response(messages, functions)

        if response.get("function_call"):
            return self._execute_function_call(response["function_call"], skip_tts)

        reply = response["content"] or "Я не понял запрос"
        self.context.add_assistant_message(reply)

        # Добавляем персонализацию в ответ
        reply = self._personalize_response(reply, text)

        if not skip_tts:
            self.tts.speak(reply)

        return reply

    def _personalize_response(self, response: str, original_query: str) -> str:
        """Добавляет персонализацию в ответ"""
        # Заменяем обращения
        response = response.replace("пользователь", OWNER_NAME)
        response = response.replace("владелец", OWNER_NAME)

        # Добавляем контекст для технических запросов
        tech_keywords = ["backend", "api", "django", "fastapi", "python", "code", "программирование"]
        if any(keyword in original_query.lower() for keyword in tech_keywords):
            if "как" in original_query.lower() or "помоги" in original_query.lower():
                response += " Как backend разработчик, ты знаешь что делаешь, шеф."

        # Спортивные запросы
        sport_keywords = ["спорт", "тренировка", "лыжи", "плавание", "футбол", "командный"]
        if any(keyword in original_query.lower() for keyword in sport_keywords):
            response = response.replace("хорошо", "отлично, для спортсмена твоего уровня")

        # Учебные запросы
        if "учеба" in original_query.lower() or "венгрия" in original_query.lower():
            response += " Удачи в учебе в Веспреме!"

        return response

    def _execute_function_call(self, func_call: Dict[str, Any], skip_tts: bool) -> str:
        func_name = func_call["name"]
        params = func_call["arguments"]

        logger.info(f"[{OWNER_NAME}] Вызов функции: {func_name} с параметрами {params}")

        # Проверка безопасности
        if SafetyChecker.needs_confirmation(func_name, params):
            self.awaiting_confirmation = True
            self.pending_function = (func_name, params)
            reply = f"{OWNER_NAME}, действие '{func_name}' требует подтверждения. Скажи 'да' для выполнения или 'нет' для отмены."
            self.tts.speak(reply)
            return reply

        return self._run_function(func_name, params, skip_tts)

    def _run_function(self, name: str, params: dict, skip_tts: bool = False) -> str:
        result = self.registry.execute(name, params)

        result_str = json.dumps(result, ensure_ascii=False)
        self.context.add_function_result(name, result_str)

        if result["success"]:
            reply = result["message"]
        else:
            reply = f"Ошибка выполнения: {result['message']}"

        # Получаем финальный ответ от LLM с результатом функции
        messages = self.context.get_messages_for_llm()
        final_response = self.llm.get_response(messages, functions=None)

        if final_response["content"]:
            reply = final_response["content"]

        # Персонализируем ответ
        reply = self._personalize_response(reply, f"function:{name}")

        self.context.add_assistant_message(reply)

        if not skip_tts:
            self.tts.speak(reply)

        return reply

    def _handle_confirmation(self, text: str) -> str:
        text_lower = text.lower().strip()

        if any(word in text_lower for word in ["да", "yes", "конечно", "выполни"]):
            self.awaiting_confirmation = False
            func_name, params = self.pending_function
            self.pending_function = None
            return self._run_function(func_name, params)

        elif any(word in text_lower for word in ["нет", "no", "отмена", "не надо"]):
            self.awaiting_confirmation = False
            self.pending_function = None
            reply = f"Хорошо, {OWNER_NAME}, действие отменено"
            self.tts.speak(reply)
            return reply

        else:
            reply = f"{OWNER_NAME}, пожалуйста, скажи 'да' или 'нет'"
            self.tts.speak(reply)
            return reply

    def listen_and_process(self) -> Optional[str]:
        text = self.stt.listen()
        if not text:
            return None

        return self.process_text(text)

    def run_interactive(self):
        self.running = True
        print(f"🎙️ {VOICE_ASSISTANT_NAME} активирован для {OWNER_NAME}!")
        print("Скажите что-нибудь или нажмите Ctrl+C для выхода")
        print(f"Язык: {settings.LANGUAGE}")

        # Персонализированное приветствие
        greeting = self._get_greeting()

        # Виводимо в консоль
        print(f"🤖: {greeting}")

        # Озвучуємо привітання
        self.tts.speak(greeting)

        try:
            while self.running:
                result = self.listen_and_process()
                if result:
                    print(f"🤖: {result}")
        except KeyboardInterrupt:
            print(f"\n👋 До свидания, {OWNER_NAME}!")
            self.tts.speak(f"До свидания, {OWNER_NAME}! Буду ждать твоих команд.")
            self.stop()
        except Exception as e:
            logger.exception("Ошибка в интерактивном режиме")
            self.tts.speak("Произошла ошибка, перезапускаюсь...")
            self.run_interactive()

    def run_text_mode(self):
        print(f"💬 Текстовый режим {VOICE_ASSISTANT_NAME} (exit для выхода, 'стоп' для остановки TTS)")
        print(f"Доступные функции: {', '.join(self.registry.list_functions())}")
        print(f"Привет, {OWNER_NAME}! Готов к работе.")

        # Озвучуємо привітання в текстовому режимі
        greeting = self._get_greeting()
        self.tts.speak(greeting)

        while True:
            try:
                text = input(f"\n{OWNER_NAME} > ").strip()

                if text.lower() in ["exit", "quit", "выход"]:
                    break
                elif text.lower() in ["стоп", "stop"]:
                    self.tts.stop()
                    continue
                elif text.lower() == "очистить":
                    self.context.clear()
                    print("Контекст очищен")
                    continue
                elif text.lower() == "привет":
                    greeting = self._get_greeting()
                    print(f"🤖: {greeting}")
                    self.tts.speak(greeting)  # Озвучуємо привітання на команду "привет"
                    continue

                if not text:
                    continue

                response = self.process_text(text, skip_tts=True)
                print(f"🤖: {response}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception("Ошибка текстового режима")
                print(f"🤖: Ошибка: {e}")

        print(f"👋 До свидания, {OWNER_NAME}!")

    def run_with_hotkey(self):
        """Фоновий режим з активацією по Ctrl+Alt+J"""
        from pynput import keyboard
        import time

        logger.info(f"🎙️ {VOICE_ASSISTANT_NAME} запущен в фоновом режиме")
        logger.info(f"Активация: {settings.ACTIVATION_KEY}")

        # Стан помічника
        self.listening_active = False
        self.last_activation = 0
        self.cooldown_period = 2

        def on_activate():
            """Обработчик активации"""
            current_time = time.time()

            if current_time - self.last_activation < self.cooldown_period:
                return

            if self.listening_active:
                return

            self.last_activation = current_time
            self.listening_active = True

            logger.info("🎤 Активация Jarvis!")

            try:
                self.tts.speak("Слушаю", priority=True)
                text = self.stt.listen(timeout=8, phrase_time_limit=12)

                if text:
                    logger.info(f"👤 {OWNER_NAME}: {text}")

                    if self._handle_special_commands(text):
                        return

                    response = self.process_text(text)
                    logger.info(f"🤖 Jarvis: {response}")

                    if len(response) > 200:
                        self._speak_long_response(response)
                    else:
                        self.tts.speak(response)
                else:
                    self.tts.speak("Не расслышал, повтори", priority=True)

            except Exception as e:
                logger.error(f"Ошибка: {e}")
                self.tts.speak("Произошла ошибка", priority=True)
            finally:
                self.listening_active = False

        try:
            # Парсимо комбінацію клавіш
            hotkey = keyboard.HotKey(
                keyboard.HotKey.parse(settings.ACTIVATION_KEY),
                on_activate
            )

            # Додаткові комбінації для виходу
            exit_combination = {keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('q')}
            emergency_combination = {keyboard.Key.ctrl_l, keyboard.KeyCode.from_char('x')}

            pressed_keys = set()

            def on_press(key):
                """Обработчик нажатия клавиш"""
                pressed_keys.add(key)

                # Перевірка аварійного виходу
                if emergency_combination.issubset(pressed_keys):
                    self.tts.speak("Аварийное выключение!")
                    self.stop()
                    return False

                # Перевірка звичайного виходу
                if exit_combination.issubset(pressed_keys):
                    logger.info("Получена команда выхода")
                    self.tts.speak(f"До свидания, {OWNER_NAME}!")
                    self.stop()
                    return False

                hotkey.press(listener.canonical(key))

            def on_release(key):
                """Обработчик отпускания клавиш"""
                pressed_keys.discard(key)
                hotkey.release(listener.canonical(key))

            # Запускаем listener
            with keyboard.Listener(
                    on_press=on_press,
                    on_release=on_release,
                    suppress=False
            ) as listener:

                logger.info("Jarvis готов к работе!")
                logger.info("Советы:")
                logger.info(f"  - Нажми {settings.ACTIVATION_KEY} для активации")
                logger.info("  - Ctrl+Q для выхода")
                logger.info("  - Ctrl+X для аварийного выхода")

                # === ОЗВУЧУЄМО ПРИВІТАННЯ ===
                greeting = self._get_greeting()
                self.tts.speak(f"{OWNER_NAME}, Jarvis активирован и готов к работе! {greeting}")

                # Чекаємо подій
                listener.join()

        except KeyboardInterrupt:
            logger.info("Прервано пользователем")
            self.tts.speak(f"До свидания, {OWNER_NAME}!")

        except Exception as e:
            logger.exception(f"Ошибка в hotkey режиме: {e}")
            self.tts.speak("Произошла ошибка, перезапускаюсь...")
            time.sleep(2)
            self.run_with_hotkey()  # Перезапуск

        finally:
            if self.running:
                self.stop()

    def stop(self):
        logger.info(f"Остановка {VOICE_ASSISTANT_NAME} для {OWNER_NAME}")
        self.running = False
        self.tts.stop()
        logger.info("Помощник остановлен")