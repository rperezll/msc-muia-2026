from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


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

    @abstractmethod
    def chat_structured(
        self, messages: list[dict[str, str]], schema: type[T], **kwargs
    ) -> tuple[T, dict[str, int]]:
        """LLM con structured output + usage"""
        ...
