import json
import logging
import requests
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config.settings import settings
from config.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY не установлен!")
                raise ValueError("Необходим OPENAI_API_KEY")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"Инициализирован OpenAI клиент, модель: {settings.LLM_MODEL}")
        else:
            logger.info(f"Используется локальная LLM: {settings.LOCAL_LLM_URL}")

    def get_response(self, messages: List[Dict], functions: List[Dict] = None, temperature: float = 0.7) -> Dict[
        str, Any]:
        if self.provider == "openai":
            return self._openai_call(messages, functions, temperature)
        else:
            return self._local_call(messages, functions)

    def _openai_call(self, messages: List[Dict], functions: List[Dict], temperature: float) -> Dict[str, Any]:
        try:
            # Формируем параметры
            params = {
                "model": settings.LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 500,
            }

            # Добавляем functions в старом формате (совместимость)
            if functions:
                params["functions"] = functions
                params["function_call"] = "auto"

            logger.debug(f"Отправка запроса: {json.dumps(params, ensure_ascii=False, indent=2)}")

            response = self.client.chat.completions.create(**params)
            choice = response.choices[0]

            result = {
                "content": choice.message.content or "",
                "function_call": None,
                "finish_reason": choice.finish_reason
            }

            # Обработка function_call (старый формат)
            if hasattr(choice.message, 'function_call') and choice.message.function_call:
                result["function_call"] = {
                    "name": choice.message.function_call.name,
                    "arguments": json.loads(choice.message.function_call.arguments)
                }
                logger.info(f"Function call detected: {result['function_call']}")

            return result

        except Exception as e:
            logger.exception("Ошибка OpenAI API")
            return {
                "content": "Извините, произошла ошибка при обработке запроса",
                "function_call": None,
                "finish_reason": "error"
            }

    def _local_call(self, messages: List[Dict], functions: List[Dict]) -> Dict[str, Any]:
        try:
            prompt = self._build_local_prompt(messages, functions)

            response = requests.post(
                f"{settings.LOCAL_LLM_URL}/api/generate",
                json={
                    "model": settings.LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=30
            )
            response.raise_for_status()

            result_text = response.json()["response"]

            try:
                parsed = json.loads(result_text)
                if "functions" in parsed:
                    return {
                        "content": parsed.get("response", ""),
                        "function_call": parsed["functions"][0] if parsed["functions"] else None,
                        "finish_reason": "stop"
                    }
            except json.JSONDecodeError:
                pass

            return {
                "content": result_text,
                "function_call": None,
                "finish_reason": "stop"
            }

        except Exception as e:
            logger.exception("Ошибка локальной LLM")
            return {
                "content": f"Ошибка: {str(e)}",
                "function_call": None,
                "finish_reason": "error"
            }

    def _build_local_prompt(self, messages: List[Dict], functions: List[Dict]) -> str:
        lines = [SYSTEM_PROMPT, ""]

        if functions:
            lines.append("Доступные функции:")
            for func in functions:
                lines.append(f"- {func['name']}: {func['description']}")
            lines.append("")

        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")

            if role == "system":
                lines.append(f"System: {content}")
            elif role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "function":
                name = msg.get("name", "unknown")
                lines.append(f"Function {name}: {content}")

        lines.append("Assistant:")
        return "\n".join(lines)