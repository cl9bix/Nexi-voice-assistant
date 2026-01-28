from .system_funcs import ScreenshotFunction, VolumeControlFunction, SystemInfoFunction
from .app_funcs import OpenAppFunction, TypeTextFunction, PressKeyFunction
from .media_funcs import MediaControlFunction, BrightnessFunction
from .file_funcs import SearchFileFunction

ALL_FUNCTIONS = [
    ScreenshotFunction(),
    VolumeControlFunction(),
    SystemInfoFunction(),
    OpenAppFunction(),
    TypeTextFunction(),
    PressKeyFunction(),
    MediaControlFunction(),
    BrightnessFunction(),
    SearchFileFunction(),
]