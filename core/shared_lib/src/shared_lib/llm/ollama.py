from typing import TypeVar

import requests
from pydantic import BaseModel

from shared_lib.llm._base_llm import BaseLLM, LLMResponse

T = TypeVar("T", bound=BaseModel)


def _parse_ollama_usage(data: dict) -> dict[str, int]:
    if "prompt_eval_count" not in data:
        return {}
    return {
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "completion_tokens": data.get("eval_count", 0),
        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
    }


class Ollama(BaseLLM):
    def __init__(self, model: str, base_url: str | None = None, **kwargs):
        self.model = model
        self.base_url = base_url or "http://localhost:11434"

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return self.chat_with_usage(messages, **kwargs).content

    def chat_with_usage(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        payload = {"model": self.model, "messages": messages, "stream": False, **kwargs}
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                usage=_parse_ollama_usage(data),
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con Ollama en {self.base_url}. Error: {e}") from e

    def chat_structured(
        self, messages: list[dict[str, str]], schema: type[T], **kwargs
    ) -> tuple[T, dict[str, int]]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": schema.model_json_schema(),
            **kwargs,
        }
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            return schema.model_validate_json(content), _parse_ollama_usage(data)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con Ollama en {self.base_url}. Error: {e}") from e

    def embed(self, texts: list[str], model: str) -> list[float]:
        try:
            response = requests.post(
                f"{self.base_url}/api/embed", json={"model": model, "input": texts}
            )
            response.raise_for_status()
            embeddings = response.json()["embeddings"]
            n = len(embeddings)
            return [sum(e[i] for e in embeddings) / n for i in range(len(embeddings[0]))]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con Ollama en {self.base_url}. Error: {e}") from e
