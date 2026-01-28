from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from config.settings import settings


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    function_call: Optional[Dict] = None
    name: Optional[str] = None


class ContextManager:
    def __init__(self):
        self.messages: List[Message] = []
        self.system_prompt = ""

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt
        if self.messages and self.messages[0].role == "system":
            self.messages[0].content = prompt
        else:
            self.messages.insert(0, Message("system", prompt))

    def add_user_message(self, content: str):
        self.messages.append(Message("user", content))
        self._trim_context()

    def add_assistant_message(self, content: str, function_call=None):
        self.messages.append(Message("assistant", content, function_call=function_call))
        self._trim_context()

    def add_function_result(self, function_name: str, result: str):
        # Для role='function' нужно имя функции
        content = f"Результат: {result}"
        self.messages.append(Message("function", content, name=function_name))

    def get_messages_for_llm(self) -> List[Dict]:
        """Формат для OpenAI API"""
        result = []
        for m in self.messages:
            msg = {"role": m.role, "content": m.content}

            # Для function role добавляем name
            if m.role == "function" and m.name:
                msg["name"] = m.name

            # Для assistant с function_call
            if m.function_call and m.role == "assistant":
                msg["function_call"] = m.function_call

            result.append(msg)

        return result

    def _trim_context(self):
        max_messages = settings.MAX_CONTEXT_MESSAGES
        if len(self.messages) > max_messages + 1:
            self.messages = [self.messages[0]] + self.messages[-max_messages:]

    def clear(self):
        self.messages = []
        if self.system_prompt:
            self.messages.append(Message("system", self.system_prompt))

    def get_last_n(self, n: int) -> List[Message]:
        return self.messages[-n:]