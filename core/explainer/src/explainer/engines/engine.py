import json
import time

from shared_lib.config import config
from shared_lib.llm import create_llm
from shared_lib.logger import get_logger
from shared_lib.schemas.anomaly import AnomalyReport, LLMAnalysis

from ..audit import AuditLogger, AuditRecord
from ..prompts import SYSTEM
from ._base import BaseEngine, ProgressCallback
from .preprocess import preprocess

log = get_logger("explainer")


def _tokens_per_second(completion_tokens: int | None, llm_ms: int) -> float | None:
    if completion_tokens and llm_ms > 0:
        return round(completion_tokens / (llm_ms / 1000), 1)
    return None


class ExplainerEngine(BaseEngine):
    """Preprocesamiento determinista + structured output LLM + ensamblado final"""

    def __init__(self) -> None:
        self._cfg = config.explainer
        self._llm = create_llm(
            provider=self._cfg.llm_provider,
            model=self._cfg.target_model,
            api_key=self._cfg.api_key,
            base_url=self._cfg.base_url,
            runpod_url=self._cfg.runpod_url,
        )
        self._audit = AuditLogger(path=self._cfg.audit_path)

    def run(self, user_query: str, context: str, on_progress: ProgressCallback = None) -> str:
        report = AnomalyReport.model_validate_json(context)
        t_start = time.perf_counter()

        # Preprocesamiento determinista
        if on_progress:
            on_progress(1, 2)

        t0 = time.perf_counter()
        summary, event_data = preprocess(report)
        preprocess_ms = int((time.perf_counter() - t0) * 1000)
        log.debug("Fase 1 completada en %dms", preprocess_ms)

        # Ejecución de LLM con structured output
        if on_progress:
            on_progress(2, 2)

        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": summary},
        ]

        t1 = time.perf_counter()
        try:
            analysis, usage = self._llm.chat_structured(
                messages=messages,
                schema=LLMAnalysis,
                temperature=self._cfg.temperature,
            )
        except Exception as e:
            llm_ms = int((time.perf_counter() - t1) * 1000)
            total_ms = int((time.perf_counter() - t_start) * 1000)
            self._audit.write(
                AuditRecord(
                    report_id=report.report_id,
                    source_key=report.source_key,
                    provider=self._cfg.llm_provider,
                    model=self._cfg.target_model,
                    temperature=self._cfg.temperature,
                    preprocess_ms=preprocess_ms,
                    llm_ms=llm_ms,
                    total_ms=total_ms,
                    prompt_tokens=None,
                    completion_tokens=None,
                    total_tokens=None,
                    tokens_per_second=None,
                    prompt_chars=len(summary),
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
            )
            log.error("Error en llamada LLM structured: %s", e)
            raise

        llm_ms = int((time.perf_counter() - t1) * 1000)
        total_ms = int((time.perf_counter() - t_start) * 1000)
        completion_tokens = usage.get("completion_tokens")
        log.debug("Fase 2 completada en %dms con %d tokens", llm_ms, usage.get("total_tokens", 0))

        self._audit.write(
            AuditRecord(
                report_id=report.report_id,
                source_key=report.source_key,
                provider=self._cfg.llm_provider,
                model=self._cfg.target_model,
                temperature=self._cfg.temperature,
                preprocess_ms=preprocess_ms,
                llm_ms=llm_ms,
                total_ms=total_ms,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=completion_tokens,
                total_tokens=usage.get("total_tokens"),
                tokens_per_second=_tokens_per_second(completion_tokens, llm_ms),
                prompt_chars=len(summary),
                status="ok",
                anomaly_type=analysis.anomaly_type,
                affected_subsystem=analysis.affected_subsystem,
                summary=analysis.summary,
                rag_queries=analysis.suggested_rag_search_queries,
            )
        )

        # Ensamblado final
        incident = {
            "event_metadata": {
                "timestamp": event_data["timestamp"],
                "severity": event_data["severity"],
                "instance_id": report.source_key,
            },
            "rag_search_parameters": {
                "generic_component_class": "Solar Inverter",
                "anomaly_type": analysis.anomaly_type,
                "affected_subsystem": analysis.affected_subsystem,
            },
            "technical_description": {
                "original_metrics": event_data["metrics"],
                "summary": analysis.summary,
            },
            "suggested_rag_search_queries": analysis.suggested_rag_search_queries,
        }
        return json.dumps([incident], indent=2, default=str)
