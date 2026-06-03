from typing import Protocol, runtime_checkable

from knowledge.schemas import RagDocument


@runtime_checkable
class Retriever(Protocol):
    def search(self, queries: list[str], top_k: int) -> list[RagDocument]: ...


class NullRetriever:
    """En desarrollo"""

    def search(self, queries: list[str], top_k: int) -> list[RagDocument]:
        return []
