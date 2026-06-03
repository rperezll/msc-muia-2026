import json
import time
from typing import TypeVar

import requests
from pydantic import BaseModel

from shared_lib.llm._base_llm import BaseLLM, LLMResponse
from shared_lib.logger import get_logger

log = get_logger("llm")

T = TypeVar("T", bound=BaseModel)


def _parse_ollama_usage(chunk: dict) -> dict[str, int]:
    if "prompt_eval_count" not in chunk:
        return {}
    return {
        "prompt_tokens": chunk.get("prompt_eval_count", 0),
        "completion_tokens": chunk.get("eval_count", 0),
        "total_tokens": chunk.get("prompt_eval_count", 0) + chunk.get("eval_count", 0),
    }


def _stream_ollama(base_url: str, payload: dict) -> tuple[str, dict[str, int]]:
    """Consume un stream Ollama/RunPod y devuelve (content, usage)"""

    t0 = time.perf_counter()
    log.debug("[runpod] Enviando request a %s (stream)", base_url)
    response = requests.post(f"{base_url}/api/chat", json=payload, stream=True, timeout=300)
    response.raise_for_status()

    content_parts: list[str] = []
    last_chunk: dict = {}
    token_count = 0
    for line in response.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        token = chunk.get("message", {}).get("content", "")
        if token:
            content_parts.append(token)
            token_count += 1
            if token_count == 1:
                log.debug("[runpod] Primer token recibido (%.1fs)", time.perf_counter() - t0)
        if chunk.get("done"):
            last_chunk = chunk

    log.debug("[runpod] Completado: %d tokens en %.1fs", token_count, time.perf_counter() - t0)
    return "".join(content_parts), _parse_ollama_usage(last_chunk)


class Runpod(BaseLLM):
    def __init__(self, model: str, base_url: str, **kwargs):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return self.chat_with_usage(messages, **kwargs).content

    def chat_with_usage(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        payload = {"model": self.model, "messages": messages, "stream": True, **kwargs}
        try:
            content, usage = _stream_ollama(self.base_url, payload)
            return LLMResponse(content=content, usage=usage)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con RunPod en {self.base_url}. Error: {e}") from e

    def chat_structured(
        self, messages: list[dict[str, str]], schema: type[T], **kwargs
    ) -> tuple[T, dict[str, int]]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "format": schema.model_json_schema(),
            **kwargs,
        }
        try:
            content, usage = _stream_ollama(self.base_url, payload)
            return schema.model_validate_json(content), usage
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con RunPod en {self.base_url}. Error: {e}") from e
