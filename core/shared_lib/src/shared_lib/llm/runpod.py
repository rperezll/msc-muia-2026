import time
from typing import TypeVar

import requests
from pydantic import BaseModel

from shared_lib.llm._base_llm import BaseLLM, LLMResponse
from shared_lib.logger import get_logger

log = get_logger("llm")

T = TypeVar("T", bound=BaseModel)


def _extract_openai_usage(usage: dict) -> dict[str, int]:
    """El worker serverless de RunPod devuelve una estructura openai-friendly"""
    if not usage:
        return {}
    return {
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }


def _unwrap_output(data: dict) -> dict:
    output = data.get("output")
    if isinstance(output, list):
        if not output:
            raise Exception(f"Output vacío de RunPod: {data}")
        output = output[0]
    if not isinstance(output, dict):
        raise Exception(f"Output inesperado de RunPod: {output!r}")
    if "error" in output:
        raise Exception(f"Error del worker RunPod: {output['error']}")
    return output


class Runpod(BaseLLM):
    """Worker serverless svenbrnn/runpod-ollama"""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None = None,
        poll_interval: float = 2.0,
        max_wait: float = 600.0,
        **kwargs,
    ):
        self.model = model
        # base_url = https://api.runpod.ai/v2/{endpoint_id}
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.poll_interval = poll_interval
        self.max_wait = max_wait

    @property
    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _post(self, openai_input: dict) -> dict:
        payload = {
            "input": {
                "openai_route": "/v1/chat/completions",
                "openai_input": {"model": self.model, "stream": False, **openai_input},
            }
        }
        t0 = time.perf_counter()
        try:
            # Encola el job para ser resiliente a cold start
            resp = requests.post(
                f"{self.base_url}/run", json=payload, headers=self._headers, timeout=30
            )
            resp.raise_for_status()
            job_id = resp.json()["id"]
            log.debug("[runpod] Job encolado %s", job_id)

            while True:
                if time.perf_counter() - t0 > self.max_wait:
                    raise Exception(f"Timeout ({self.max_wait}s) esperando job {job_id}")
                time.sleep(self.poll_interval)
                st = requests.get(
                    f"{self.base_url}/status/{job_id}", headers=self._headers, timeout=30
                )
                st.raise_for_status()
                data = st.json()
                status = data.get("status")
                if status == "COMPLETED":
                    break
                if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
                    raise Exception(f"Job RunPod {status}: {data}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con RunPod en {self.base_url}: {e}") from e

        chat = _unwrap_output(data)
        log.debug("[runpod] Completado en %.1fs", time.perf_counter() - t0)
        return chat

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return self.chat_with_usage(messages, **kwargs).content

    def chat_with_usage(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        chat = self._post({"messages": messages, **kwargs})
        content = chat["choices"][0]["message"]["content"] or ""
        return LLMResponse(content=content, usage=_extract_openai_usage(chat.get("usage", {})))

    def chat_structured(
        self, messages: list[dict[str, str]], schema: type[T], **kwargs
    ) -> tuple[T, dict[str, int]]:
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()},
        }
        chat = self._post({"messages": messages, "response_format": response_format, **kwargs})
        content = chat["choices"][0]["message"]["content"] or ""
        return schema.model_validate_json(content), _extract_openai_usage(chat.get("usage", {}))

    def embed(self, texts: list[str], model: str) -> list[float]:
        raise NotImplementedError("RunPod no soporta embeddings")
