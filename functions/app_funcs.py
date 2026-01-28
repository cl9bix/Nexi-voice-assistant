import subprocess
import platform
import pyautogui
from .base import BaseFunction, FunctionResult


class OpenAppFunction(BaseFunction):
    name = "open_application"
    description = "Открывает программу по названию"
    parameters = {
        "app_name": {"type": "string", "description": "Название программы (chrome, calculator, notepad, etc)"}
    }

    APP_MAP = {
        "chrome": {"Windows": "chrome", "Darwin": "Google Chrome", "Linux": "google-chrome"},
        "firefox": {"Windows": "firefox", "Darwin": "Firefox", "Linux": "firefox"},
        "edge": {"Windows": "msedge", "Darwin": "Microsoft Edge", "Linux": "microsoft-edge"},
        "notepad": {"Windows": "notepad", "Darwin": "TextEdit", "Linux": "gedit"},
        "calculator": {"Windows": "calc", "Darwin": "Calculator", "Linux": "gnome-calculator"},
        "calc": {"Windows": "calc", "Darwin": "Calculator", "Linux": "gnome-calculator"},
        "terminal": {"Windows": "cmd", "Darwin": "Terminal", "Linux": "gnome-terminal"},
        "explorer": {"Windows": "explorer", "Darwin": "Finder", "Linux": "nautilus"},
        "spotify": {"Windows": "spotify", "Darwin": "Spotify", "Linux": "spotify"},
        "discord": {"Windows": "discord", "Darwin": "Discord", "Linux": "discord"},
        "telegram": {"Windows": "telegram", "Darwin": "Telegram", "Linux": "telegram-desktop"},
        "code": {"Windows": "code", "Darwin": "Visual Studio Code", "Linux": "code"},
        "vscode": {"Windows": "code", "Darwin": "Visual Studio Code", "Linux": "code"},
    }

    def execute(self, app_name: str) -> FunctionResult:
        system = platform.system()
        app_key = app_name.lower()

        if app_key in self.APP_MAP:
            cmd = self.APP_MAP[app_key].get(system, app_name)
        else:
            cmd = app_name

        try:
            if system == "Windows":
                subprocess.Popen(cmd, shell=True)
            elif system == "Darwin":
                subprocess.Popen(["open", "-a", cmd])
            else:
                subprocess.Popen([cmd])

            return FunctionResult(True, f"Открываю {app_name}")
        except Exception as e:
            return FunctionResult(False, f"Не удалось открыть {app_name}: {e}")


class TypeTextFunction(BaseFunction):
    name = "type_text"
    description = "Печатает текст в активном окне"
    parameters = {
        "text": {"type": "string", "description": "Текст для печати"},
        "interval": {"type": "number", "description": "Интервал между символами", "default": 0.01}
    }

    def execute(self, text: str, interval: float = 0.01) -> FunctionResult:
        try:
            pyautogui.typewrite(text, interval=interval)
            return FunctionResult(True, f"Напечатано: {text[:50]}...")
        except Exception as e:
            return FunctionResult(False, str(e))


class PressKeyFunction(BaseFunction):
    name = "press_key"
    description = "Нажимает клавишу или комбинацию (enter, ctrl+c, alt+tab, etc)"
    parameters = {
        "key": {"type": "string", "description": "Клавиша или комбинация"},
        "presses": {"type": "integer", "description": "Количество нажатий", "default": 1}
    }

    def execute(self, key: str, presses: int = 1) -> FunctionResult:
        try:
            pyautogui.press(key, presses=presses)
            return FunctionResult(True, f"Нажато {key}")
        except Exception as e:
            return FunctionResult(False, str(e))