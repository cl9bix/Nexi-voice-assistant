# test_openai_tts.py
import os
from openai import OpenAI
from pathlib import Path
import subprocess

print("🎯 Тест OpenAI TTS для Юрия")

# Встанови свій ключ
os.environ["OPENAI_API_KEY"] = "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"

try:
    client = OpenAI()

    print("✅ OpenAI клиент инициализирован")

    # Генеруємо тестовий файл
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input="Юрий, это тест OpenAI TTS. Если ты слышишь меня, значит все работает отлично!"
    )

    # Зберігаємо тимчасовий файл
    temp_file = Path("test_openai.mp3")
    response.stream_to_file(str(temp_file))

    print(f"✅ Аудио файл создан: {temp_file}")
    print("🔊 Воспроизвожду...")

    # Відтворюємо
    os.startfile(str(temp_file))

    print("✅ Тест OpenAI TTS завершен!")

except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\nНажми Enter для выхода...")
input()