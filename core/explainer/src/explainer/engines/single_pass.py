import json
import time

from shared_lib.config import config
from shared_lib.logger import get_logger
from shared_lib.schemas.anomaly import AnomalyDetection, AnomalyReport

from ..audit import AuditLogger
from ..llm._llm_factory import create_llm
from ..prompts import SYSTEM_SINGLE_PASS
from ._base import BaseEngine, ProgressCallback

log = get_logger("explainer")


def _classify_severity(mae: float | None, threshold: float | None) -> str:
    if mae is None or threshold is None or threshold == 0:
        return "LOW"
    ratio = mae / threshold
    if ratio >= 2.0:
        return "CRITICAL"
    if ratio >= 1.5:
        return "HIGH"
    if ratio >= 1.2:
        return "MEDIUM"
    return "LOW"


def _irradiation_category(irr: float) -> str:
    if irr <= 0.01:
        return "night"
    if irr < 0.3:
        return "low"
    if irr < 0.7:
        return "medium"
    return "high"


def _compute_detection_metrics(det: AnomalyDetection) -> dict:
    """Calcula métricas con los datos de una detección"""

    p = det.payload
    dc = p.DC_POWER
    ac = p.AC_POWER
    efficiency = (ac / dc * 100) if dc > 0 else 0.0

    is_lstm = det.mae is not None and det.threshold is not None
    mae_ratio = det.mae / det.threshold if is_lstm and det.threshold > 0 else None

    return {
        "detection_id": det.detection_id,
        "timestamp": det.timestamp.isoformat(),
        "mae": round(det.mae, 4) if det.mae is not None else None,
        "threshold": round(det.threshold, 4) if det.threshold is not None else None,
        "mae_over_threshold_pct": (
            round((mae_ratio - 1) * 100, 1) if mae_ratio is not None else None
        ),
        "severity": _classify_severity(det.mae, det.threshold),
        "dc_power": round(dc, 1),
        "ac_power": round(ac, 1),
        "dc_ac_efficiency_pct": round(efficiency, 1),
        "module_temperature": round(p.MODULE_TEMPERATURE, 1),
        "ambient_temperature": round(p.AMBIENT_TEMPERATURE, 1),
        "temp_delta": round(p.MODULE_TEMPERATURE - p.AMBIENT_TEMPERATURE, 1),
        "irradiation": round(p.IRRADIATION, 3),
        "irradiation_category": _irradiation_category(p.IRRADIATION),
        "daily_yield": round(p.DAILY_YIELD, 1),
    }


_SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _group_by_pattern(metrics_list: list[dict]) -> list[dict]:
    """Agrupa detecciones por el mismo contexto solar (irradiación)"""

    groups: dict[str, list[dict]] = {}
    for m in metrics_list:
        groups.setdefault(m["irradiation_category"], []).append(m)

    result = []
    for irr_cat, members in groups.items():
        mae_values = [m["mae"] for m in members if m["mae"] is not None]
        avg_mae = sum(mae_values) / len(mae_values) if mae_values else None
        avg_eff = sum(m["dc_ac_efficiency_pct"] for m in members) / len(members)
        avg_temp_delta = sum(m["temp_delta"] for m in members) / len(members)
        threshold = next((m["threshold"] for m in members if m["threshold"] is not None), None)
        # severidad máxima del grupo
        severity = max(members, key=lambda m: _SEVERITY_RANK.get(m["severity"], 0))["severity"]

        result.append(
            {
                "group_key": irr_cat,
                "count": len(members),
                "irradiation_category": irr_cat,
                "severity": severity,
                "avg_mae": round(avg_mae, 4) if avg_mae is not None else None,
                "threshold": threshold,
                "avg_dc_ac_efficiency_pct": round(avg_eff, 1),
                "avg_temp_delta": round(avg_temp_delta, 1),
                "time_range": {
                    "first": members[0]["timestamp"],
                    "last": members[-1]["timestamp"],
                },
                "detection_ids": [m["detection_id"] for m in members],
            }
        )
    return result


def _build_skeleton(group: dict, source_key: str) -> dict:
    """Construye el esqueleto JSON con campos prerellenados y marcadores __LLM__"""
    return {
        "event_metadata": {
            "timestamp": group["time_range"]["first"],
            "severity": group["severity"],
            "instance_id": source_key,
        },
        "rag_search_parameters": {
            "generic_component_class": "Solar Inverter",
            "anomaly_type": "__LLM__",
            "affected_subsystem": "__LLM__",
        },
        "technical_description": {
            "original_metrics": {
                "mae": group["avg_mae"],
                "threshold": group.get("threshold"),
                "dc_ac_efficiency_pct": group["avg_dc_ac_efficiency_pct"],
                "avg_temp_delta": group["avg_temp_delta"],
                "irradiation_category": group["irradiation_category"],
                "detection_count": group["count"],
            },
            "summary": "__LLM__",
        },
        "suggested_rag_search_queries": "__LLM__",
    }


def _dominant_group(groups: list[dict]) -> dict:
    """Selecciona el grupo de mayor gravedad y en caso de empate elige el de mayor avg_mae"""
    return max(groups, key=lambda g: (_SEVERITY_RANK.get(g["severity"], 0), g["avg_mae"] or 0))


def preprocess(report: AnomalyReport) -> tuple[str, list[dict]]:
    """Genera resumen textual y un único esqueleto JSON del grupo dominante"""
    metrics = [_compute_detection_metrics(d) for d in report.detections]
    groups = _group_by_pattern(metrics)
    dominant = _dominant_group(groups)
    skeletons = [_build_skeleton(dominant, report.source_key)]

    lines = [
        f"Report: {report.report_id}",
        f"Inverter: {report.source_key}",
        f"Total detections: {len(report.detections)}",
        f"Groups detected: {len(groups)} (showing dominant group for classification)",
        "",
    ]
    for g in groups:
        marker = " [DOMINANT]" if g is dominant else ""
        lines.append(
            f"- Group [{g['group_key']}]{marker}: {g['count']} detections, "
            f"severity={g['severity']}, irr={g['irradiation_category']}, "
            f"avg_mae={g['avg_mae']}, avg_eff={g['avg_dc_ac_efficiency_pct']}%, "
            f"avg_temp_delta={g['avg_temp_delta']}°C, "
            f"range={g['time_range']['first']} to {g['time_range']['last']}"
        )

    lines.append("")
    lines.append("JSON skeleton to complete (fill __LLM__ fields):")
    lines.append(json.dumps(skeletons, indent=2, default=str))

    summary = "\n".join(lines)
    return summary, skeletons


def _merge_llm_output(skeletons: list[dict], llm_output: str) -> list[dict]:
    """Parsea la salida del LLM y fusiona con los esqueletos precalculados"""
    try:
        llm_data = json.loads(llm_output)
    except json.JSONDecodeError:
        import re

        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", llm_output, re.DOTALL)
        if match:
            llm_data = json.loads(match.group(1))
        else:
            log.warning("No se pudo parsear la salida del LLM, usando esqueletos sin LLM")
            return _apply_fallback(skeletons)

    if not isinstance(llm_data, list) or len(llm_data) != len(skeletons):
        log.warning(
            "Longitud de salida LLM (%s) != esqueletos (%d), aplicando fallback",
            len(llm_data) if isinstance(llm_data, list) else "N/A",
            len(skeletons),
        )
        return _apply_fallback(skeletons)

    merged = []
    for skeleton, llm_item in zip(skeletons, llm_data, strict=False):
        result = json.loads(json.dumps(skeleton))
        rag = llm_item.get("rag_search_parameters", {})
        result["rag_search_parameters"]["anomaly_type"] = (
            rag.get("anomaly_type") or "unknown_anomaly"
        )
        result["rag_search_parameters"]["affected_subsystem"] = (
            rag.get("affected_subsystem") or "Unknown Subsystem"
        )

        td = llm_item.get("technical_description", {})
        summary = td.get("summary")
        result["technical_description"]["summary"] = (
            summary
            if isinstance(summary, str) and summary.strip()
            else (
                f"Anomaly detected with severity {skeleton['event_metadata']['severity']}."
                " No summary generated."
            )
        )

        queries = llm_item.get("suggested_rag_search_queries")
        if isinstance(queries, list) and queries:
            result["suggested_rag_search_queries"] = queries[:3]
        else:
            result["suggested_rag_search_queries"] = ["solar inverter anomaly diagnosis"] * 3
        merged.append(result)

    return merged


def _apply_fallback(skeletons: list[dict]) -> list[dict]:
    """Rellena los campos __LLM__ con valores genéricos de fallback"""
    results = []
    for s in skeletons:
        result = json.loads(json.dumps(s))
        result["rag_search_parameters"]["anomaly_type"] = "unclassified_anomaly"
        result["rag_search_parameters"]["affected_subsystem"] = "Unknown Subsystem"
        result["technical_description"]["summary"] = (
            f"Anomaly detected with severity {s['event_metadata']['severity']}."
            " No summary generated."
        )
        result["suggested_rag_search_queries"] = ["solar inverter anomaly diagnosis"]
        results.append(result)
    return results


class SinglePassEngine(BaseEngine):
    """Preprocesamiento determinista + llamada LLM + merge"""

    def __init__(self) -> None:
        self._cfg = config.explainer
        self._auditor = AuditLogger(engine_mode="single_pass")
        self._llm = create_llm(self._cfg)

    def run(self, user_query: str, context: str, on_progress: ProgressCallback = None) -> str:
        report = AnomalyReport.model_validate_json(context)
        self._auditor.start_session(
            self._cfg.target_model,
            user_query,
            len(context),
            report_id=report.report_id,
            source_key=report.source_key,
        )

        # preprocesamiento determinista
        if on_progress:
            on_progress(1, 3)

        t0 = time.perf_counter()
        summary, skeletons = preprocess(report)
        preprocess_time = time.perf_counter() - t0
        log.debug("Fase 1 completada en %.3fs — %d grupos", preprocess_time, len(skeletons))

        self._auditor.add_step(
            step=1,
            thought="[pre-procesamiento determinista]",
            repl_output=summary[:2000],
            action="preprocess",
            duration_s=preprocess_time,
        )

        # llamada LLM
        if on_progress:
            on_progress(2, 3)

        messages = [
            {"role": "system", "content": SYSTEM_SINGLE_PASS},
            {"role": "user", "content": summary},
        ]

        try:
            t1 = time.perf_counter()
            llm_response = self._llm.chat_with_usage(
                messages=messages,
                temperature=self._cfg.temperature,
            )
            llm_time = time.perf_counter() - t1
            log.debug(
                "Fase 2 completada en %.1fs — %d tokens",
                llm_time,
                llm_response.usage.get("total_tokens", 0),
            )

            self._auditor.add_step(
                step=2,
                thought=llm_response.content[:2000],
                repl_output="",
                action="llm_single_call",
                tokens=llm_response.usage,
                duration_s=llm_time,
            )
        except Exception as e:
            log.error("Error en llamada LLM single-pass: %s", e)
            self._auditor.close_session(status="api_error", total_steps=2, fatal_error=str(e))
            raise

        # merge y validación
        if on_progress:
            on_progress(3, 3)

        t2 = time.perf_counter()
        incidents = _merge_llm_output(skeletons, llm_response.content)
        merge_time = time.perf_counter() - t2

        result = json.dumps(incidents, indent=2, default=str)
        log.debug("Fase 3 completada en %.3fs — %d incidentes", merge_time, len(incidents))

        self._auditor.add_step(
            step=3,
            thought="[merge y validación]",
            repl_output=result[:2000],
            action="merge_validate",
            duration_s=merge_time,
        )

        self._auditor.close_session(status="success", total_steps=3, final_result=result)
        return result
