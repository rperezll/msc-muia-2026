import json
import time

import requests

from shared_lib.logger import get_logger

from ._base_llm import BaseLLM, LLMResponse

log = get_logger("explainer")


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
            t0 = time.perf_counter()
            log.debug("[runpod] Enviando request a %s (stream)", self.base_url)
            response = requests.post(
                f"{self.base_url}/api/chat", json=payload, stream=True, timeout=300
            )
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
                        ttft = time.perf_counter() - t0
                        log.debug("[runpod] Primer token recibido (%.1fs)", ttft)
                if chunk.get("done"):
                    last_chunk = chunk

            elapsed = time.perf_counter() - t0
            log.debug("[runpod] Completado: %d tokens en %.1fs", token_count, elapsed)

            usage = {}
            if "prompt_eval_count" in last_chunk:
                usage = {
                    "prompt_tokens": last_chunk.get("prompt_eval_count", 0),
                    "completion_tokens": last_chunk.get("eval_count", 0),
                    "total_tokens": last_chunk.get("prompt_eval_count", 0)
                    + last_chunk.get("eval_count", 0),
                }
            return LLMResponse(content="".join(content_parts), usage=usage)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con RunPod en {self.base_url}. Error: {e}") from e
