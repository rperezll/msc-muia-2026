import json
import os
from datetime import datetime
from typing import Any
from uuid import uuid4

from shared_lib.logger import get_logger

log = get_logger("explainer")


class AuditLogger:
    """Registra la ejecución del engine en formato JSONL para trazabilidad"""

    def __init__(self, engine_mode: str, audit_file: str = "logs/audit.jsonl"):
        self.engine_mode = engine_mode
        self.audit_file = audit_file
        os.makedirs(os.path.dirname(self.audit_file), exist_ok=True)
        self._current: dict | None = None

    def start_session(
        self,
        model: str,
        user_query: str,
        context_length: int,
        report_id: str = "",
        source_key: str = "",
    ) -> None:
        self._current = {
            "session_id": uuid4().hex,
            "engine_mode": self.engine_mode,
            "report_id": report_id,
            "source_key": source_key,
            "timestamp_start": datetime.now().isoformat(),
            "model": model,
            "user_query": user_query,
            "context_length": context_length,
            "iterations": [],
            "final_result": None,
            "status": "in_progress",
            "total_steps": 0,
            "total_tokens_session": 0,
            "fatal_error": None,
        }

    def add_step(
        self,
        step: int,
        thought: str,
        repl_output: str,
        action: str,
        tokens: dict[str, int] | None = None,
        duration_s: float | None = None,
    ) -> None:
        if self._current is None:
            return
        step_tokens = tokens or {}
        self._current["total_tokens_session"] += step_tokens.get("total_tokens", 0)
        self._current["iterations"].append(
            {
                "step": step,
                "model_thought": thought,
                "repl_output": repl_output,
                "action": action,
                "tokens": step_tokens,
                "duration_s": round(duration_s, 2) if duration_s is not None else None,
            }
        )

    def close_session(
        self,
        status: str,
        total_steps: int,
        final_result: Any = None,
        fatal_error: str | None = None,
    ) -> None:
        if self._current is None:
            return
        self._current["status"] = status
        self._current["total_steps"] = total_steps
        self._current["final_result"] = final_result
        if fatal_error:
            self._current["fatal_error"] = fatal_error

        end_time = datetime.now()
        start_time = datetime.fromisoformat(self._current["timestamp_start"])
        self._current["timestamp_end"] = end_time.isoformat()
        self._current["duration_seconds"] = (end_time - start_time).total_seconds()

        self._save()
        self._current = None

    def _save(self) -> None:
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(self._current, ensure_ascii=False) + "\n")
        except Exception as e:
            log.error("Error guardando auditoría: %s", e)
