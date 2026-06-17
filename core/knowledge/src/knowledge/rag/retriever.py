from typing import Protocol, runtime_checkable

from knowledge.schemas import RagDocument
from shared_lib.db.postgres import PostgresTransport
from shared_lib.llm import BaseLLM
from shared_lib.logger import get_logger

log = get_logger("knowledge.retriever")

_SEARCH_SQL = """
    SELECT title, content, source, 1 - (embedding <=> %s::vector) AS score
    FROM documents
    ORDER BY embedding <=> %s::vector
    LIMIT %s
"""


@runtime_checkable
class Retriever(Protocol):
    def search(self, queries: list[str], top_k: int) -> list[RagDocument]: ...


class NullRetriever:
    def search(self, queries: list[str], top_k: int) -> list[RagDocument]:
        return []


class VectorRetriever:
    def __init__(
        self,
        transport: PostgresTransport,
        llm: BaseLLM,
        embedding_model: str,
    ) -> None:
        self._transport = transport
        self._llm = llm
        self._model = embedding_model

    def _embed_queries(self, queries: list[str]) -> list[float]:
        # Media de los embeddings para multi query
        return self._llm.embed(queries, self._model)

    def search(self, queries: list[str], top_k: int) -> list[RagDocument]:
        if not queries:
            return []
        embedding = self._embed_queries(queries)
        vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
        log.debug("VectorRetriever: top_%d para %d queries", top_k, len(queries))
        with self._transport.cursor() as cur:
            cur.execute(_SEARCH_SQL, (vec_str, vec_str, top_k))
            rows = cur.fetchall()
        return [
            RagDocument(title=row[0], snippet=row[1], source=row[2], score=float(row[3]))
            for row in rows
        ]
