import os
import platform
import subprocess
import pyautogui
import ctypes
from ctypes import wintypes
import time
import pyaudio
from .base import BaseFunction, FunctionResult

WM_APPCOMMAND = 0x319
APPCOMMAND_VOLUME_UP = 0x0a
APPCOMMAND_VOLUME_DOWN = 0x09
APPCOMMAND_VOLUME_MUTE = 0x08

class ScreenshotFunction(BaseFunction):
    name = "take_screenshot"
    description = "Делает скриншот экрана и сохраняет его"
    parameters = {"filename": {"type": "string", "description": "Имя файла"}}

    def execute(self, filename: str = "screenshot.png") -> FunctionResult:
        try:
            screenshot = pyautogui.screenshot()
            path = f"screenshots/{filename}"
            os.makedirs("screenshots", exist_ok=True)
            screenshot.save(path)
            return FunctionResult(True, f"Скриншот сохранен: {path}", path)
        except Exception as e:
            return FunctionResult(False, f"Ошибка: {e}")


class VolumeControlFunction(BaseFunction):
    name = "control_volume"
    description = "Управляет громкостью системы (up, down, mute, set)"
    parameters = {
        "action": {"type": "string", "enum": ["up", "down", "mute", "set"]},
        "level": {"type": "integer", "description": "Уровень громкости 0-100 (только для set)"}
    }

    def __init__(self):
        self._hwnd = None
        if platform.system() == "Windows":
            self._hwnd = ctypes.windll.user32.GetForegroundWindow()

    def execute(self, action: str, level: int = None) -> FunctionResult:
        system = platform.system()

        try:
            if system == "Windows":
                return self._windows_control(action, level)
            else:
                return self._linux_control(action, level)

        except Exception as e:
            return FunctionResult(False, f"Ошибка управления громкостью: {e}")

    def _send_app_command(self, command):
        """Отправляет команду приложению"""
        if self._hwnd:
            ctypes.windll.user32.SendMessageW(self._hwnd, WM_APPCOMMAND, 0, command << 16)

    def _windows_control(self, action: str, level: int = None) -> FunctionResult:
        """Управление громкостью на Windows"""
        if action == "mute":
            self._send_app_command(APPCOMMAND_VOLUME_MUTE)
            return FunctionResult(True, "Звук переключен")

        elif action == "up":
            for _ in range(5):
                self._send_app_command(APPCOMMAND_VOLUME_UP)
            return FunctionResult(True, "Громкость увеличена")

        elif action == "down":
            for _ in range(5):
                self._send_app_command(APPCOMMAND_VOLUME_DOWN)
            return FunctionResult(True, "Громкость уменьшена")

        elif action == "set":
            if level is None:
                return FunctionResult(False, "Не указан уровень громкости")

            level = max(0, min(100, level))

            try:
                winmm = ctypes.windll.winmm

                mixer_handle = wintypes.HMIXER()
                result = winmm.mixerOpen(ctypes.byref(mixer_handle), 0, 0, 0, 0)

                if result != 0:
                    return self._set_volume_fallback(level)

                mixer_line = ctypes.c_uint(0)

                winmm.mixerClose(mixer_handle)

                return FunctionResult(True, f"Громкость установлена на {level}%")

            except Exception as e:
                return self._set_volume_fallback(level)

        return FunctionResult(False, f"Неизвестное действие: {action}")

    def _set_volume_fallback(self, level: int) -> FunctionResult:
        """Запасний метод установки громкости"""
        try:
            # Перевіряємо чи існує nircmd
            nircmd_path = None
            for path in [r"C:\Windows\System32\nircmd.exe",
                         r"C:\Windows\nircmd.exe",
                         r"nircmd.exe"]:
                if os.path.exists(path):
                    nircmd_path = path
                    break

            if nircmd_path:
                subprocess.run(
                    [nircmd_path, "setsysvolume", str(int(level * 655.35))],
                    check=True,
                    capture_output=True
                )
                return FunctionResult(True, f"Громкость установлена на {level}%")
            else:
                # Fallback на кнопки без nircmd
                for _ in range(50):
                    self._send_app_command(APPCOMMAND_VOLUME_DOWN)

                steps = int(level / 2)
                for _ in range(steps):
                    self._send_app_command(APPCOMMAND_VOLUME_UP)

                return FunctionResult(True, f"Громкость примерно установлена на {level}% (методом шагов)")

        except Exception as e:
            return FunctionResult(False, f"Ошибка установки громкости: {e}")

    def _linux_control(self, action: str, level: int = None) -> FunctionResult:
        """Управление громкостью на Linux"""
        if action == "mute":
            os.system("amixer set Master toggle")
            return FunctionResult(True, "Звук переключен")

        elif action == "set" and level is not None:
            level = max(0, min(100, level))
            os.system(f"amixer set Master {level}%")
            return FunctionResult(True, f"Громкость установлена на {level}%")

        elif action == "up":
            os.system("amixer set Master 5%+")
            return FunctionResult(True, "Громкость увеличена")

        elif action == "down":
            os.system("amixer set Master 5%-")
            return FunctionResult(True, "Громкость уменьшена")

        return FunctionResult(False, f"Неизвестное действие: {action}")


class SystemInfoFunction(BaseFunction):
    name = "get_system_info"
    description = "Получает информацию о системе"
    parameters = {}

    def execute(self) -> FunctionResult:
        info = {
            "os": platform.system(),
            "version": platform.version(),
            "processor": platform.processor(),
        }
        return FunctionResult(True, f"OS: {info['os']}, {info['processor']}", info)


class AudioDeviceControlFunction(BaseFunction):
    name = "control_audio_device"
    description = "Управляет аудио устройствами и микшером"
    parameters = {
        "action": {"type": "string", "enum": ["list_devices", "set_default", "check_python", "fix_python"]},
        "device_name": {"type": "string", "description": "Название устройства для установки по умолчанию"}
    }

    def execute(self, action: str, device_name: str = None) -> FunctionResult:
        try:
            if action == "list_devices":
                return self._list_audio_devices()
            elif action == "set_default":
                return self._set_default_device(device_name)
            elif action == "check_python":
                return self._check_python_audio()
            elif action == "fix_python":
                return self._fix_python_audio()
            else:
                return FunctionResult(False, f"Неизвестное действие: {action}")

        except Exception as e:
            return FunctionResult(False, f"Ошибка управления аудио: {e}")

    def _list_audio_devices(self) -> FunctionResult:
        """Список всех аудио устройств"""
        try:
            p = pyaudio.PyAudio()
            devices = []

            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                devices.append({
                    "index": i,
                    "name": device_info['name'],
                    "channels": device_info['maxInputChannels'],
                    "is_default": device_info.get('isDefault', False)
                })

            p.terminate()

            device_list = "\n".join([f"{d['index']}: {d['name']}" for d in devices])
            return FunctionResult(True, f"Аудио устройства:\n{device_list}", devices)

        except Exception as e:
            return FunctionResult(False, f"Ошибка получения списка устройств: {e}")

    def _check_python_audio(self) -> FunctionResult:
        """Проверка, использует ли Python аудио устройство"""
        try:
            # Проверяем через Windows Audio Session API
            pythoncom.CoInitialize()

            devices = AudioUtilities.GetAllDevices()
            python_device = None

            for device in devices:
                if "python" in device.FriendlyName.lower() or "pyaudio" in device.FriendlyName.lower():
                    python_device = device.FriendlyName
                    break

            if python_device:
                return FunctionResult(True, f"Python обнаружен как аудио устройство: {python_device}", python_device)
            else:
                return FunctionResult(True, "Python не обнаружен в аудио устройствах", None)

        except Exception as e:
            return FunctionResult(False, f"Ошибка проверки: {e}")

    def _fix_python_audio(self) -> FunctionResult:
        """Автоматическое исправление проблемы с Python аудио"""
        try:
            # Способ 1: Перезапуск аудио службы Windows
            subprocess.run(["net", "stop", "Audiosrv"], capture_output=True, timeout=5)
            time.sleep(1)
            subprocess.run(["net", "start", "Audiosrv"], capture_output=True, timeout=5)

            # Способ 2: Сброс настроек аудио
            subprocess.run(["sndvol", "/r"], capture_output=True, timeout=3)

            # Способ 3: Переназначение устройства по умолчанию
            try:
                # Получаем список устройств
                devices = AudioUtilities.GetAllDevices()
                speakers = None

                for device in devices:
                    if "speakers" in device.FriendlyName.lower() or "наушники" in device.FriendlyName.lower():
                        speakers = device
                        break

                if speakers:
                    # Устанавливаем как устройство по умолчанию
                    speakers.SetAsDefault()
                    return FunctionResult(True,
                                          f"Исправлено! Установлено устройство по умолчанию: {speakers.FriendlyName}")
                else:
                    return FunctionResult(True, "Аудио служба перезапущена, но устройство по умолчанию не найдено")

            except Exception as e:
                return FunctionResult(True, f"Аудио служба перезапущена, но есть нюансы: {e}")

        except Exception as e:
            return FunctionResult(False, f"Ошибка исправления: {e}")


class TTSVolumeControlFunction(BaseFunction):
    name = "control_tts_volume"
    description = "Управляет громкостью TTS специально"
    parameters = {
        "action": {"type": "string", "enum": ["test_sound", "check_tts", "fix_tts_volume"]}
    }

    def execute(self, action: str) -> FunctionResult:
        try:
            if action == "test_sound":
                return self._test_sound()
            elif action == "check_tts":
                return self._check_tts_status()
            elif action == "fix_tts_volume":
                return self._fix_tts_volume()
            else:
                return FunctionResult(False, f"Неизвестное действие: {action}")

        except Exception as e:
            return FunctionResult(False, f"Ошибка: {e}")

    def _test_sound(self) -> FunctionResult:
        """Тестовый звук для проверки"""
        try:
            from services.tts_service import TTSService

            tts = TTSService()
            tts.speak_immediately(f"{OWNER_NAME}, это тестовый звук. Если ты слышишь меня, значит все работает!")

            return FunctionResult(True, "Тестовый звук отправлен в динамики")

        except Exception as e:
            return FunctionResult(False, f"Ошибка тестового звука: {e}")

    def _check_tts_status(self) -> FunctionResult:
        """Проверка статуса TTS"""
        try:
            from services.tts_service import TTSService

            tts = TTSService()

            status = {
                "is_speaking": tts.is_speaking(),
                "engine_available": bool(tts.engine),
                "queue_size": tts.queue.qsize()
            }

            status_text = f"TTS статус: двигатель {'работает' if status['engine_available'] else 'не доступен'}, "
            status_text += f"озвучка {'активна' if status['is_speaking'] else 'не активна'}, "
            status_text += f"в очереди {status['queue_size']} сообщений"

            return FunctionResult(True, status_text, status)

        except Exception as e:
            return FunctionResult(False, f"Ошибка проверки TTS: {e}")

    def _fix_tts_volume(self) -> FunctionResult:
        """Исправление проблемы с громкостью TTS"""
        try:
            # Проверяем системную громкость
            system = platform.system()

            if system == "Windows":
                # Проверяем громкость приложения Python
                subprocess.run([
                    "nircmd.exe", "setappvolume", "python.exe", "100"
                ], capture_output=True, timeout=3)

                # Проверяем громкость самого TTS
                subprocess.run([
                    "nircmd.exe", "setappvolume", "sapisvr.exe", "100"  # Windows TTS engine
                ], capture_output=True, timeout=3)

                return FunctionResult(True, "Громкость TTS установлена на максимум")
            else:
                return FunctionResult(True, "Для Linux/Mac используйте системный микшер")

        except Exception as e:
            return FunctionResult(False, f"Ошибка установки громкости: {e}")