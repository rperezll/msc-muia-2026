import json as _json
import re
import time

from shared_lib.config import config
from shared_lib.logger import get_logger

from ..audit import AuditLogger
from ..llm._llm_factory import create_llm
from ..prompts import SYSTEM_RLM
from ._base import BaseEngine, ProgressCallback
from .repl import PythonREPL

log = get_logger("explainer")


class RLMEngine(BaseEngine):
    """LLM razona, ejecuta código en el REPL e itera hasta usar FINAL"""

    def __init__(self) -> None:
        self._cfg = config.explainer
        self._auditor = AuditLogger(engine_mode="rlm")
        self._llm = create_llm(self._cfg)
        self._history: list[dict[str, str]] = []

    def run(self, user_query: str, context: str, on_progress: ProgressCallback = None) -> str:
        meta = _json.loads(context)
        self._auditor.start_session(
            self._cfg.target_model,
            user_query,
            len(context),
            report_id=meta.get("report_id", ""),
            source_key=meta.get("source_key", ""),
        )

        context_preview = context[:1000].replace("\n", "\\n")
        context_meta = (
            f"ANOMALY REPORT: The global variable `context` (type str, JSON) "
            f"is loaded in memory with {len(context)} characters. "
            f"It contains the AnomalyReport from the LSTM detector.\n"
            f'- Preview (start): "{context_preview}..."'
        )

        self._history = [
            {"role": "system", "content": SYSTEM_RLM},
            {"role": "system", "content": context_meta},
            {"role": "user", "content": f"Main Query: {user_query}"},
        ]

        repl = PythonREPL(context)
        log.debug("Iniciando RLM con modelo: %s", self._cfg.target_model)

        for i in range(self._cfg.max_iterations):
            step = i + 1
            log.debug("--- Iteración %d/%d ---", step, self._cfg.max_iterations)

            if on_progress:
                on_progress(step, self._cfg.max_iterations)

            try:
                t0 = time.perf_counter()
                llm_response = self._llm.chat_with_usage(
                    messages=self._history,
                    temperature=self._cfg.temperature,
                    stop=["<STOP_TOKEN>"],
                )
                step_duration = time.perf_counter() - t0
                content = llm_response.content
                step_tokens = llm_response.usage
                self._history.append({"role": "assistant", "content": content})
                log.debug("Pensamiento del modelo:\n%s", content)

            except Exception as e:
                log.error("Error en llamada al LLM: %s", e)
                self._auditor.close_session(
                    status="api_error", total_steps=step, fatal_error=str(e)
                )
                raise

            # FINAL_VAR(variable_name)
            var_match = re.search(r"FINAL_VAR\((.*?)\)", content)
            if var_match:
                var_name = var_match.group(1).strip()
                if var_name in repl.globals:
                    raw = repl.globals[var_name]
                    try:
                        final_val = _json.dumps(raw, indent=2, default=str)
                    except (TypeError, ValueError):
                        final_val = str(raw)
                    display = (
                        final_val
                        if len(final_val) <= 5000
                        else final_val[:5000] + "\n... [truncado]"
                    )
                    log.debug("Resultado final (variable %s):\n%s", var_name, display)
                    self._auditor.add_step(
                        step,
                        content,
                        "",
                        f"finished_with_variable_{var_name}",
                        tokens=step_tokens,
                        duration_s=step_duration,
                    )
                    self._auditor.close_session(
                        status="success", total_steps=step, final_result=final_val
                    )
                    return final_val
                else:
                    feedback = (
                        f"Error: you tried to return FINAL_VAR({var_name}) "
                        "but that variable does not exist."
                    )
                    log.warning(feedback)
                    self._history.append({"role": "user", "content": feedback})
                    self._auditor.add_step(
                        step,
                        content,
                        feedback,
                        "error_variable_not_found",
                        tokens=step_tokens,
                        duration_s=step_duration,
                    )
                    continue

            # Texto directo
            if "FINAL:" in content:
                final_answer = content.split("FINAL:")[-1].strip()
                log.debug("Resultado final (texto):\n%s", final_answer)
                self._auditor.add_step(
                    step,
                    content,
                    "",
                    "finished_with_text",
                    tokens=step_tokens,
                    duration_s=step_duration,
                )
                self._auditor.close_session(
                    status="success_fallback", total_steps=step, final_result=final_answer
                )
                return final_answer

            # Bloque de código python
            code_match = re.search(r"```(?:python|repl)\n(.*?)\n```", content, re.DOTALL)
            if code_match:
                code = code_match.group(1)
                log.debug("Ejecutando código en REPL...")
                output = repl.execute(code)
                display_output = (
                    output
                    if len(output) <= 2000
                    else output[:2000] + f"\n... [truncado, {len(output)} chars]"
                )
                log.debug("REPL output:\n%s", display_output)
                feedback = f"Result (stdout):\n{display_output}"
                if not output.strip():
                    feedback += (
                        "\n(No stdout output. Use print() if you need to see data ,"
                        "or assume that variables were saved)."
                    )
                self._history.append({"role": "user", "content": feedback})
                self._auditor.add_step(
                    step,
                    content,
                    output,
                    "execute_code",
                    tokens=step_tokens,
                    duration_s=step_duration,
                )
            else:
                feedback = (
                    "No code block detected. "
                    "Use ```python ... ``` or end with 'FINAL:' or 'FINAL_VAR(...)'"
                )
                self._history.append({"role": "user", "content": feedback})
                self._auditor.add_step(
                    step,
                    content,
                    feedback,
                    "error_no_code",
                    tokens=step_tokens,
                    duration_s=step_duration,
                )

        self._auditor.close_session(
            status="max_iterations_reached", total_steps=self._cfg.max_iterations
        )
        return "Max iterations reached."
