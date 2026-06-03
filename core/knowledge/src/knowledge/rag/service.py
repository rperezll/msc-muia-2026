from knowledge.rag.retriever import Retriever
from shared_lib.config import RagConfig
from shared_lib.llm import BaseLLM
from shared_lib.logger import get_logger
from shared_lib.schemas import AugmentResponse, RagDocument

log = get_logger("knowledge")

_AUGMENT_SYSTEM = (
    "You are an expert in photovoltaic solar systems. "
    "You receive an anomaly summary and relevant technical documentation. "
    "Generate a technically grounded, augmented explanation based on the documentation. "
    "If no documentation is available, reason solely from the summary."
)


def _build_augment_prompt(
    summary: str,
    queries: list[str],
    docs: list[RagDocument],
) -> str:
    parts = [f"## Anomaly summary\n{summary}", "## RAG queries used"]
    parts.extend(f"- {q}" for q in queries)
    if docs:
        parts.append("## Retrieved documentation")
        for d in docs:
            parts.append(f"### {d.title or 'Document'} ({d.source or ''})")
            parts.append(d.snippet)
    return "\n\n".join(parts)


class RagService:
    def __init__(self, llm: BaseLLM, retriever: Retriever, cfg: RagConfig) -> None:
        self._llm = llm
        self._retriever = retriever
        self._cfg = cfg

    def augment(
        self,
        summary: str,
        rag_queries: list[str],
    ) -> AugmentResponse:
        docs = self._retriever.search(rag_queries, self._cfg.top_k)
        log.debug("RAG: %d queries, %d docs recuperados", len(rag_queries), len(docs))

        prompt = _build_augment_prompt(summary, rag_queries, docs)
        messages = [
            {"role": "system", "content": _AUGMENT_SYSTEM},
            {"role": "user", "content": prompt},
        ]
        augmented = self._llm.chat(messages, temperature=self._cfg.temperature)

        return AugmentResponse(
            augmented_summary=augmented,
            retrieved=docs,
            model=self._cfg.llm_model,
        )
