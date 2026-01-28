#!/usr/bin/env python3
import sys
import os
import logging
import argparse
from pathlib import Path
from config.prompts import VOICE_ASSISTANT_NAME, OWNER_NAME

# Додаємо корінь проєкту в шлях
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from config.settings import LOGS_DIR, settings


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    file_handler = logging.FileHandler(
        LOGS_DIR / "assistant.log",
        encoding='utf-8',
        mode='a'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Активация {VOICE_ASSISTANT_NAME} для {OWNER_NAME}")
    logger.info(f"Конфигурация: LLM={settings.LLM_PROVIDER}, Lang={settings.LANGUAGE}")


def check_dependencies():
    try:
        import speech_recognition
        import pyautogui
        import pyttsx3
        import openai
        import pynput
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите: pip install -r requirements.txt")
        return False


def main():
    parser = argparse.ArgumentParser(
        description=f"{VOICE_ASSISTANT_NAME} - голосовой помощник для {OWNER_NAME}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Режимы работы для {OWNER_NAME}:
  voice   - Непрерывное прослушивание (по умолчанию)
  hotkey  - Активация по клавише F13
  text    - Текстовый режим для тестирования

Примеры команд для {OWNER_NAME}:
  - "Jarvis, открой браузер"
  - "Джарвис, поставь громкость на 50"
  - "открой калькулятор"
  - "сделай скриншот"
        """
    )
    parser.add_argument(
        "--mode",
        choices=["voice", "hotkey", "text"],
        default="voice",
        help="Режим работы помощника"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Включить отладочный вывод"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not check_dependencies():
        sys.exit(1)

    setup_logging()

    try:
        from core.assistant import VoiceAssistant

        assistant = VoiceAssistant()

        if args.mode == "voice":
            assistant.run_interactive()
        elif args.mode == "hotkey":
            assistant.run_with_hotkey()
        elif args.mode == "text":
            assistant.run_text_mode()

    except KeyboardInterrupt:
        print(f"\n👋 До свидания, {OWNER_NAME}!")
    except Exception as e:
        logging.exception("Критическая ошибка")
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()