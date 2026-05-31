from datetime import datetime

import pytest

from explainer.engines.preprocess import (
    _classify_severity,
    _compute_detection_metrics,
    _dominant_group,
    _group_by_pattern,
    _irradiation_category,
    preprocess,
)
from test_utils.builders import make_anomaly_report, make_detection


class TestClasificaSeveridad:
    def test_critico_ratio_exacto(self):
        assert _classify_severity(1.0, 0.5) == "CRITICAL"

    def test_critico_ratio_mayor(self):
        assert _classify_severity(2.0, 0.5) == "CRITICAL"

    def test_high_ratio_exacto(self):
        assert _classify_severity(0.75, 0.5) == "HIGH"

    def test_medium_ratio_exacto(self):
        assert _classify_severity(0.6, 0.5) == "MEDIUM"

    def test_low_ratio_menor(self):
        assert _classify_severity(0.55, 0.5) == "LOW"

    def test_mae_none(self):
        assert _classify_severity(None, 0.5) == "LOW"

    def test_threshold_none(self):
        assert _classify_severity(1.0, None) == "LOW"

    def test_threshold_cero(self):
        assert _classify_severity(1.0, 0) == "LOW"


class TestCategoriaIrradiacion:
    def test_noche_limite(self):
        assert _irradiation_category(0.01) == "night"

    def test_noche_cero(self):
        assert _irradiation_category(0.0) == "night"

    def test_baja(self):
        assert _irradiation_category(0.1) == "low"

    def test_media(self):
        assert _irradiation_category(0.5) == "medium"

    def test_alta(self):
        assert _irradiation_category(0.7) == "high"

    def test_alta_mayor(self):
        assert _irradiation_category(1.0) == "high"


class TestComputeDetectionMetrics:
    def test_eficiencia_normal(self):
        det = make_detection(DC_POWER=100.0, AC_POWER=90.0, mae=0.9, threshold=0.5)
        m = _compute_detection_metrics(det)
        assert m["dc_ac_efficiency_pct"] == 90.0

    def test_eficiencia_dc_cero(self):
        det = make_detection(DC_POWER=0.0, AC_POWER=0.0)
        m = _compute_detection_metrics(det)
        assert m["dc_ac_efficiency_pct"] == 0.0

    def test_temp_delta(self):
        det = make_detection(AMBIENT_TEMPERATURE=25.0, MODULE_TEMPERATURE=35.0)
        m = _compute_detection_metrics(det)
        assert m["temp_delta"] == 10.0

    def test_mae_over_threshold_pct(self):
        det = make_detection(mae=0.9, threshold=0.5)
        m = _compute_detection_metrics(det)
        assert m["mae_over_threshold_pct"] == 80.0

    def test_irradiation_category_en_metrics(self):
        det = make_detection(IRRADIATION=0.5)
        m = _compute_detection_metrics(det)
        assert m["irradiation_category"] == "medium"

    def test_severity_en_metrics(self):
        det = make_detection(mae=1.0, threshold=0.5)
        m = _compute_detection_metrics(det)
        assert m["severity"] == "CRITICAL"


class TestGroupByPattern:
    def test_agrupa_por_categoria_irradiacion(self):
        d1 = make_detection(IRRADIATION=0.5, mae=0.9, threshold=0.5)  # medium
        d2 = make_detection(IRRADIATION=0.1, mae=0.6, threshold=0.5)  # low
        metrics = [_compute_detection_metrics(d) for d in [d1, d2]]
        groups = _group_by_pattern(metrics)
        keys = {g["group_key"] for g in groups}
        assert keys == {"medium", "low"}

    def test_time_range_sigue_orden_lista(self):
        ts_a = datetime(2020, 6, 1, 8, 0)
        ts_b = datetime(2020, 6, 1, 7, 0)
        d1 = make_detection(timestamp=ts_a, IRRADIATION=0.5)
        d2 = make_detection(timestamp=ts_b, IRRADIATION=0.5)
        metrics = [_compute_detection_metrics(d) for d in [d1, d2]]
        groups = _group_by_pattern(metrics)
        g = groups[0]
        assert g["time_range"]["first"] == ts_a.isoformat()
        assert g["time_range"]["last"] == ts_b.isoformat()

    def test_severidad_maxima_del_grupo(self):
        d1 = make_detection(mae=0.55, threshold=0.5, IRRADIATION=0.5)  # LOW
        d2 = make_detection(mae=1.0, threshold=0.5, IRRADIATION=0.5)  # CRITICAL
        metrics = [_compute_detection_metrics(d) for d in [d1, d2]]
        groups = _group_by_pattern(metrics)
        assert groups[0]["severity"] == "CRITICAL"

    def test_avg_mae_calculado(self):
        d1 = make_detection(mae=0.6, threshold=0.5, IRRADIATION=0.5)
        d2 = make_detection(mae=0.8, threshold=0.5, IRRADIATION=0.5)
        metrics = [_compute_detection_metrics(d) for d in [d1, d2]]
        groups = _group_by_pattern(metrics)
        assert groups[0]["avg_mae"] == pytest.approx(0.7, abs=0.001)


class TestDominantGroup:
    def test_gana_mayor_severidad(self):
        grupos = [
            {"group_key": "low", "severity": "HIGH", "avg_mae": 0.5},
            {"group_key": "medium", "severity": "CRITICAL", "avg_mae": 0.3},
        ]
        dom = _dominant_group(grupos)
        assert dom["group_key"] == "medium"

    def test_empate_severidad_gana_mayor_avg_mae(self):
        grupos = [
            {"group_key": "a", "severity": "HIGH", "avg_mae": 0.9},
            {"group_key": "b", "severity": "HIGH", "avg_mae": 0.5},
        ]
        dom = _dominant_group(grupos)
        assert dom["group_key"] == "a"


class TestPreprocess:
    def test_dominant_marcado_exactamente_una_vez(self):
        report = make_anomaly_report(
            detections=[
                make_detection(mae=1.0, threshold=0.5, IRRADIATION=0.5),  # CRITICAL, medium
            ]
        )
        summary, _ = preprocess(report)
        assert summary.count("[DOMINANT]") == 1

    def test_total_detections_correcto(self):
        report = make_anomaly_report(
            detections=[
                make_detection(IRRADIATION=0.5),
                make_detection(IRRADIATION=0.1),
                make_detection(IRRADIATION=0.5),
            ]
        )
        summary, _ = preprocess(report)
        assert "Total detections: 3" in summary

    def test_event_data_tiene_severidad_grupo_dominante(self):
        report = make_anomaly_report(
            detections=[
                make_detection(mae=1.0, threshold=0.5, IRRADIATION=0.5),  # CRITICAL
                make_detection(mae=0.55, threshold=0.5, IRRADIATION=0.1),  # LOW
            ]
        )
        _, event_data = preprocess(report)
        assert event_data["severity"] == "CRITICAL"

    def test_event_data_metricas_grupo_dominante(self):
        report = make_anomaly_report(
            detections=[
                make_detection(
                    mae=1.0, threshold=0.5, IRRADIATION=0.7, DC_POWER=100.0, AC_POWER=90.0
                ),
            ]
        )
        _, event_data = preprocess(report)
        assert event_data["metrics"]["irradiation_category"] == "high"
        assert event_data["metrics"]["detection_count"] == 1

    def test_inversor_en_resumen(self):
        report = make_anomaly_report(source_key="INV_42")
        summary, _ = preprocess(report)
        assert "INV_42" in summary
