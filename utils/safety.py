from config.settings import settings


class SafetyChecker:
    @staticmethod
    def is_dangerous(command: str) -> bool:
        cmd_lower = command.lower()
        return any(danger in cmd_lower for danger in settings.DANGEROUS_COMMANDS)

    @staticmethod
    def needs_confirmation(func_name: str, params: dict) -> bool:
        if func_name in settings.REQUIRE_CONFIRMATION:
            return True
        if "command" in params:
            return SafetyChecker.is_dangerous(params["command"])
        return False

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Захист від path traversal"""
        dangerous = ["..", "~", "/etc", "/sys", "C:\\Windows", "System32"]
        return path if not any(d in path for d in dangerous) else None