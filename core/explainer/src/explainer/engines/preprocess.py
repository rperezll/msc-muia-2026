from shared_lib.schemas.anomaly import AnomalyDetection, AnomalyReport

_SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


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
    p = det.payload
    dc = p.DC_POWER
    ac = p.AC_POWER
    efficiency = (ac / dc * 100) if dc > 0 else 0.0
    mae_ratio = det.mae / det.threshold if det.mae and det.threshold else None

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


def _group_by_pattern(metrics_list: list[dict]) -> list[dict]:
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


def _dominant_group(groups: list[dict]) -> dict:
    return max(groups, key=lambda g: (_SEVERITY_RANK.get(g["severity"], 0), g["avg_mae"] or 0))


def preprocess(report: AnomalyReport) -> tuple[str, dict]:
    """Resumen textual para el LLM + métricas del grupo dominante"""

    metrics = [_compute_detection_metrics(d) for d in report.detections]
    groups = _group_by_pattern(metrics)
    dominant = _dominant_group(groups)

    event_data = {
        "timestamp": dominant["time_range"]["first"],
        "severity": dominant["severity"],
        "metrics": {
            "mae": dominant["avg_mae"],
            "threshold": dominant.get("threshold"),
            "dc_ac_efficiency_pct": dominant["avg_dc_ac_efficiency_pct"],
            "avg_temp_delta": dominant["avg_temp_delta"],
            "irradiation_category": dominant["irradiation_category"],
            "detection_count": dominant["count"],
        },
    }

    lines = [
        f"Report: {report.report_id}",
        f"Inverter: {report.source_key}",
        f"Total detections: {len(report.detections)}",
        f"Groups detected: {len(groups)} (dominant group for classification)",
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

    return "\n".join(lines), event_data
