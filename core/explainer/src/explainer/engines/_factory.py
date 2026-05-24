from shared_lib.config import ExplainerConfig

from ._base import BaseEngine


def create_engine(cfg: ExplainerConfig) -> BaseEngine:
    """Instancia el motor de explainer según engine_mode"""
    mode = cfg.engine_mode.value
    if mode == "rlm":
        from .rlm import RLMEngine

        return RLMEngine()
    if mode == "single_pass":
        from .single_pass import SinglePassEngine

        return SinglePassEngine()
    raise ValueError(f"Engine mode no soportado: '{mode}'")
