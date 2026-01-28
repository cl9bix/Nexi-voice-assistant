import pyttsx3
import re
from .tts_service import LocalTTSService


class AdvancedTTSService(LocalTTSService):
    """Покращений локальний TTS з фонетичною вимовою"""

    def _personalize_text(self, text: str) -> str:
        """Розширена персоналізація з фонетикою"""
        text = super()._personalize_text(text)

        # Фонетична вимова для кращого сприйняття
        phonetic_replacements = {
            r'\bпривет\b': 'привееет',
            r'\bПривет\b': 'Привееет',
            r'\bЮрий\b': 'Юрий',
            r'\bJarvis\b': 'Джарвис',
            r'\bпока\b': 'покааа',
            r'\bспасибо\b': 'спасииибо',
            r'\bотлично\b': 'отлииично',
            r'\bхорошо\b': 'хорошооо',
            r'\bда\b': 'даа',
            r'\bнет\b': 'нееет',
        }

        for pattern, replacement in phonetic_replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Паузи для кращого сприйняття
        text = text.replace('!', '! ')  # Трохи довша пауза після оклику
        text = text.replace('?', '? ')  # Пауза після питання

        return text

    def _configure_voice(self):
        """Налаштування з покращеними параметрами"""
        super()._configure_voice()

        # Додаткові налаштування для кращої вимови
        if self.engine:
            # Тональність (0-100, 50 = нормальна)
            self.engine.setProperty('pitch', 95)

            # Емоційна інтонація
            self.engine.setProperty('inflection', True)