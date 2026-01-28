# test_jarvis_sound.py
import pyttsx3

print("🎯 Прямой тест TTS для Юрия")
print("=" * 50)

try:
    # Ініціалізація
    engine = pyttsx3.init()
    print("✅ Pyttsx3 инициализирован")

    # Перевірка голосів
    voices = engine.getProperty('voices')
    print(f"📢 Найдено голосов: {len(voices)}")

    for i, voice in enumerate(voices):
        print(f"  Голос {i}: {voice.name} ({voice.languages if hasattr(voice, 'languages') else 'unknown'})")

    # Встановлення параметрів
    engine.setProperty('rate', 160)
    engine.setProperty('volume', 1.0)  # Максимальна гучність

    # Вибираємо перший доступний голос
    if voices:
        engine.setProperty('voice', voices[0].id)
        print(f"✅ Использую голос: {voices[0].name}")

    print("\n🔊 Тестирую звук...")
    print("Если ты слышишь: 'Юрий, это тест, я работаю!' - значит все OK")

    # Тестове повідомлення
    engine.say("Юрий, это тест, я работаю!")
    engine.runAndWait()

    print("✅ Тест завершен!")

except Exception as e:
    print(f"❌ Ошибка: {e}")
    print(f"Тип ошибки: {type(e).__name__}")

print("\nНажми Enter для выхода...")
input()