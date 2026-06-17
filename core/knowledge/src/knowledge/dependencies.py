from functools import lru_cache

from knowledge.rag.retriever import VectorRetriever
from knowledge.rag.service import RagService
from shared_lib.config import config
from shared_lib.db.postgres import PostgresTransport
from shared_lib.db.repositories.explanation import ExplanationRepository
from shared_lib.llm import create_llm


@lru_cache(maxsize=1)
def get_transport() -> PostgresTransport:
    transport = PostgresTransport(config.services.postgres)
    transport.connect()
    return transport


def get_explanation_repo() -> ExplanationRepository:
    return ExplanationRepository(get_transport())


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    cfg = config.rag
    if not cfg.api_key:
        raise RuntimeError("api_key is required but not configured")
    llm = create_llm(provider="openai", model=cfg.llm_model, api_key=cfg.api_key)
    retriever = VectorRetriever(
        transport=get_transport(),
        llm=llm,
        embedding_model=cfg.embedding_model,
    )
    return RagService(llm=llm, retriever=retriever, cfg=cfg)
