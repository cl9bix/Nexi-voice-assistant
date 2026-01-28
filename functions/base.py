from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class FunctionResult:
    success: bool
    message: str
    data: Any = None


class BaseFunction(ABC):
    name: str = ""
    description: str = ""
    parameters: Dict = {}

    @abstractmethod
    def execute(self, **kwargs) -> FunctionResult:
        pass

    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": list(self.parameters.keys())
            }
        }