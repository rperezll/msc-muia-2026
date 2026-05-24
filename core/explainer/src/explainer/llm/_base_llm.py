from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    content: str
    usage: dict[str, int] = field(default_factory=dict)


class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str: ...

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], **kwargs) -> str: ...

    def chat_with_usage(self, messages: list[dict[str, str]], **kwargs) -> LLMResponse:
        return LLMResponse(content=self.chat(messages, **kwargs))
