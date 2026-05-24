from abc import ABC, abstractmethod
from collections.abc import Callable

ProgressCallback = Callable[[int, int], None] | None


class BaseEngine(ABC):
    """Interfaz común para los motores de explainer (LLM/SLM)"""

    @abstractmethod
    def run(self, user_query: str, context: str, on_progress: ProgressCallback = None) -> str:
        """Ejecuta el análisis y devuelve el resultado como string JSON"""
        ...
