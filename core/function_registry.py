import json
import logging
from typing import List, Dict, Any
from functions.base import BaseFunction
from functions import ALL_FUNCTIONS

logger = logging.getLogger(__name__)


class FunctionRegistry:
    def __init__(self):
        self._functions: Dict[str, BaseFunction] = {}
        self._schemas: List[Dict] = []
        self._register_defaults()

    def _register_defaults(self):
        for func in ALL_FUNCTIONS:
            self.register(func)

    def register(self, func: BaseFunction):
        self._functions[func.name] = func
        self._schemas.append(func.get_schema())
        logger.info(f"Зарегистрирована функция: {func.name}")

    def get_schema(self) -> List[Dict]:
        return self._schemas

    def get_schema_json(self) -> str:
        return json.dumps(self._schemas, ensure_ascii=False, indent=2)

    def execute(self, name: str, params: Dict[str, Any]) -> Any:
        if name not in self._functions:
            logger.error(f"Функция {name} не найдена")
            return {"success": False, "message": f"Функция {name} недоступна"}

        func = self._functions[name]
        try:
            result = func.execute(**params)
            return {
                "success": result.success,
                "message": result.message,
                "data": result.data
            }
        except Exception as e:
            logger.exception(f"Ошибка выполнения {name}")
            return {"success": False, "message": str(e)}

    def list_functions(self) -> List[str]:
        return list(self._functions.keys())