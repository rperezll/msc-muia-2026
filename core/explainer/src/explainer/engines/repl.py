import contextlib
import io

from shared_lib.config import config

from ..llm._llm_factory import create_llm

# Modelo para subllamadas desde el REPL
_sub_llm = create_llm(config.explainer)


def llm_query(query: str, content_chunk: str) -> str:
    """Herramienta disponible en el REPL para consultas al submodelo LLM"""
    try:
        messages = [
            {"role": "system", "content": "You are an analysis sub-process. Be brief and precise."},
            {"role": "user", "content": f"Context: {content_chunk}\n\nQuery: {query}"},
        ]
        return _sub_llm.chat(messages=messages, temperature=0)
    except Exception as e:
        return f"Error en subllamada: {e}"


class PythonREPL:
    """REPL persistente con acceso a `context` y `llm_query`"""

    def __init__(self, context_data: str):
        self.globals: dict = {
            "context": context_data,
            "llm_query": llm_query,
            "print": print,
            "len": len,
            "range": range,
            "min": min,
            "max": max,
        }

    def execute(self, code: str) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            try:
                exec(code, self.globals)
            except Exception as e:
                print(f"Error de ejecución de código python en el REPL: {e}")
        return buffer.getvalue()
