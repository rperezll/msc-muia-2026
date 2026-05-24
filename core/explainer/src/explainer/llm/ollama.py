import requests

from ._base_llm import BaseLLM, LLMResponse


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
            usage = {}
            if "prompt_eval_count" in data:
                usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                }
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                usage=usage,
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Fallo al conectar con Ollama en {self.base_url}. Error: {e}") from e
