from shared_lib.config import LlmProvider
from shared_lib.llm._base_llm import BaseLLM
from shared_lib.llm.ollama import Ollama
from shared_lib.llm.openai import OpenAI
from shared_lib.llm.runpod import Runpod


def create_llm(
    provider: LlmProvider | str,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    runpod_url: str | None = None,
) -> BaseLLM:
    """Instancia el proveedor LLM solicitado"""
    p = str(provider)
    if p == "openai":
        return OpenAI(model=model, api_key=api_key, base_url=base_url)
    if p == "ollama":
        return Ollama(model=model, base_url=base_url)
    if p == "runpod":
        if not runpod_url:
            raise ValueError("Se requiere 'runpod_url' para el proveedor RunPod")
        return Runpod(model=model, base_url=runpod_url)
    raise ValueError(f"Proveedor LLM no soportado: '{p}'")
