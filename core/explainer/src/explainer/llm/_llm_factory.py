from shared_lib.config import ExplainerConfig

from ._base_llm import BaseLLM
from .ollama import Ollama
from .openai import OpenAI
from .runpod import Runpod


def create_llm(cfg: ExplainerConfig) -> BaseLLM:
    """Instancia el proveedor LLM configurado en ExplainerConfig"""

    provider = cfg.llm_provider.value
    if provider == "openai":
        return OpenAI(model=cfg.target_model, api_key=cfg.api_key, base_url=cfg.base_url)
    if provider == "ollama":
        return Ollama(model=cfg.target_model, base_url=cfg.base_url)
    if provider == "runpod":
        if not cfg.runpod_url:
            raise ValueError("Se requiere 'runpod_url' para el proveedor RunPod")
        return Runpod(model=cfg.target_model, base_url=cfg.runpod_url)
    raise ValueError(f"Proveedor LLM no soportado: '{provider}'")
