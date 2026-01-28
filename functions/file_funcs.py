import os
from pathlib import Path
from .base import BaseFunction, FunctionResult
from utils.safety import SafetyChecker


class SearchFileFunction(BaseFunction):
    name = "search_files"
    description = "Ищет файлы по названию"
    parameters = {
        "query": {"type": "string", "description": "Часть названия файла"},
        "location": {"type": "string", "description": "Где искать (Desktop, Documents, Downloads, Home)",
                     "default": "Home"}
    }

    def execute(self, query: str, location: str = "Home") -> FunctionResult:
        try:
            home = Path.home()
            locations = {
                "Home": home,
                "Desktop": home / "Desktop",
                "Documents": home / "Documents",
                "Downloads": home / "Downloads"
            }

            search_path = locations.get(location, home)
            if not SafetyChecker.sanitize_path(str(search_path)):
                return FunctionResult(False, "Небезопасный путь")

            matches = []
            for file in search_path.rglob(f"*{query}*"):
                if file.is_file():
                    matches.append(str(file))
                    if len(matches) >= 5:
                        break

            if matches:
                files_str = ", ".join([m.split("\\")[-1].split("/")[-1] for m in matches[:3]])
                return FunctionResult(True, f"Найдено: {files_str}", matches)
            return FunctionResult(True, "Файлы не найдены")

        except Exception as e:
            return FunctionResult(False, str(e))