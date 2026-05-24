from openai import OpenAI as OpenAIClient

from ._base_llm import BaseLLM, LLMResponse


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
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return LLMResponse(
            content=response.choices[0].message.content or "",
            usage=usage,
        )
