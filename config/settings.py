import os
from pathlib import Path
from dotenv import load_dotenv

# Завантажуємо .env з кореня проєкту
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class Settings:
    # LLM
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")

    # Audio
    LANGUAGE = os.getenv("LANGUAGE", "ru-RU")
    TTS_VOICE = os.getenv("TTS_VOICE", "russian")
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1024
    ENERGY_THRESHOLD = 300

    # Activation
    ACTIVATION_KEY = os.getenv("ACTIVATION_KEY", "<ctrl>+<alt>+j")
    # Safety
    DANGEROUS_COMMANDS = ["rm -rf", "format", "del /f", "rd /s", "sudo", ":(){ :|:& };:"]
    REQUIRE_CONFIRMATION = ["shutdown", "restart", "delete", "remove", "uninstall"]

    # Context
    MAX_CONTEXT_MESSAGES = 10

    # Timeouts
    LISTEN_TIMEOUT = 5
    PHRASE_TIME_LIMIT = 15

    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "local")  # local або openai
    TTS_VOICE_SPEED = int(os.getenv("TTS_VOICE_SPEED", "180"))  # Швидкість мови
    TTS_VOICE_PITCH = int(os.getenv("TTS_VOICE_PITCH", "95"))  # Тональність

settings = Settings()