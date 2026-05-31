from typing import TypeVar

from openai import OpenAI as OpenAIClient
from pydantic import BaseModel

from ._base_llm import BaseLLM, LLMResponse

T = TypeVar("T", bound=BaseModel)


def _extract_usage(response_usage) -> dict[str, int]:
    if not response_usage:
        return {}
    return {
        "prompt_tokens": response_usage.prompt_tokens,
        "completion_tokens": response_usage.completion_tokens,
        "total_tokens": response_usage.total_tokens,
    }


class OpenAI(BaseLLM):
    def __init__(
        self, model: str, api_key: str | None = None, base_url: str | None = None, **kwargs
    ):
        self.model = model
        self.client = OpenAIClient(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        return self.chat_with_usage(messages, **kwargs).content

    def chat_with_usage(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return LLMResponse(
            content=response.choices[0].message.content or "",
            usage=_extract_usage(response.usage),
        )

    def chat_structured(
        self, messages: list[dict[str, str]], schema: type[T], **kwargs
    ) -> tuple[T, dict[str, int]]:
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=schema,
            **kwargs,
        )
        return response.choices[0].message.parsed, _extract_usage(response.usage)
