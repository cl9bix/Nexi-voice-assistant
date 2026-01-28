import pyautogui
from .base import BaseFunction, FunctionResult


class MediaControlFunction(BaseFunction):
    name = "control_media"
    description = "Управляет воспроизведением медиа (play, pause, next, previous, stop)"
    parameters = {
        "action": {"type": "string", "enum": ["play", "pause", "next", "previous", "stop"]}
    }

    KEY_MAP = {
        "play": "playpause",
        "pause": "playpause",
        "next": "nexttrack",
        "previous": "prevtrack",
        "stop": "stop"
    }

    def execute(self, action: str) -> FunctionResult:
        try:
            key = self.KEY_MAP.get(action, action)
            pyautogui.press(key)
            return FunctionResult(True, f"Медиа: {action}")
        except Exception as e:
            return FunctionResult(False, str(e))


class BrightnessFunction(BaseFunction):
    name = "control_brightness"
    description = "Изменяет яркость экрана"
    parameters = {
        "action": {"type": "string", "enum": ["up", "down", "set"]},
        "level": {"type": "integer", "description": "Уровень 0-100"}
    }

    def execute(self, action: str, level: int = None) -> FunctionResult:
        try:
            if action == "up":
                pyautogui.press("brightnessup", presses=5)
            elif action == "down":
                pyautogui.press("brightnessdown", presses=5)
            return FunctionResult(True, f"Яркость {action}")
        except Exception as e:
            return FunctionResult(False, str(e))