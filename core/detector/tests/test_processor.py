from __future__ import annotations

import json

import pytest

from detector._processor import TelemetryProcessor
from test_utils.builders import make_telemetry_payload

from .conftest import FakeAnomalyDetector


def _make_processor(
    *,
    returns_anomaly: bool = False,
    time_steps: int = 3,
    buffer_max: int = 3,
) -> TelemetryProcessor:
    model = FakeAnomalyDetector(time_steps=time_steps, returns_anomaly=returns_anomaly)
    return TelemetryProcessor(models={1: model}, anomaly_buffer_max=buffer_max)


def _raw(payload=None) -> bytes:
    return (payload or make_telemetry_payload()).model_dump_json().encode()


def _fill(processor: TelemetryProcessor, n: int, payload=None) -> None:
    for _ in range(n):
        processor.process(_raw(payload))


class TestPayloadInvalido:
    def test_json_roto_devuelve_none(self):
        assert _make_processor().process(b"not json") is None

    def test_campo_faltante_devuelve_none(self):
        assert _make_processor().process(json.dumps({"PLANT_ID": 1}).encode()) is None


class TestVentanaDeslizante:
    def test_ventana_incompleta_devuelve_none(self):
        p = _make_processor(time_steps=3, returns_anomaly=True, buffer_max=1)
        assert p.process(_raw()) is None
        assert p.process(_raw()) is None

    def test_ventana_completa_sin_anomalia_devuelve_none(self):
        p = _make_processor(time_steps=3)
        _fill(p, 2)
        assert p.process(_raw()) is None

    def test_inversores_tienen_ventanas_independientes(self):
        p = _make_processor(time_steps=3, returns_anomaly=True, buffer_max=1)
        inv_a = make_telemetry_payload(SOURCE_KEY="INV_A")
        inv_b = make_telemetry_payload(SOURCE_KEY="INV_B")
        for _ in range(2):
            p.process(inv_a.model_dump_json().encode())
            p.process(inv_b.model_dump_json().encode())
        # Cada inversor necesita 3 mensajes propios para completar su ventana
        assert p.process(inv_a.model_dump_json().encode()) is not None
        assert p.process(inv_b.model_dump_json().encode()) is not None


class TestAnomalyBuffer:
    def test_anomalia_acumula_hasta_max(self):
        p = _make_processor(time_steps=1, returns_anomaly=True, buffer_max=3)
        assert p.process(_raw()) is None
        assert p.process(_raw()) is None
        assert p.process(_raw()) is not None

    def test_reporte_contiene_source_key_y_detecciones(self):
        p = _make_processor(time_steps=1, returns_anomaly=True, buffer_max=2)
        p.process(_raw())
        report = p.process(_raw())
        assert report is not None
        assert report.source_key == "TEST_INV"
        assert len(report.detections) == 2

    def test_lectura_normal_hace_flush_del_buffer_pendiente(self):
        model = FakeAnomalyDetector(time_steps=1, returns_anomaly=True)
        p = TelemetryProcessor(models={1: model}, anomaly_buffer_max=5)
        p.process(_raw())
        model._returns_anomaly = False
        report = p.process(_raw())
        assert report is not None
        assert len(report.detections) == 1

    def test_lectura_normal_sin_buffer_previo_devuelve_none(self):
        assert _make_processor(time_steps=1).process(_raw()) is None

    def test_deteccion_incluye_mae_y_threshold(self):
        model = FakeAnomalyDetector(time_steps=1, returns_anomaly=True, score=0.9)
        p = TelemetryProcessor(models={1: model}, anomaly_buffer_max=1)
        report = p.process(_raw())
        assert report is not None
        detection = report.detections[0]
        assert detection.mae == pytest.approx(0.9, abs=1e-5)
        assert detection.threshold == pytest.approx(0.5, abs=1e-5)


class TestPlantIdFallback:
    def test_plant_id_desconocido_usa_planta_1_sin_excepcion(self):
        model = FakeAnomalyDetector(time_steps=1)
        p = TelemetryProcessor(models={1: model}, anomaly_buffer_max=3)
        payload = make_telemetry_payload(PLANT_ID=99)
        assert p.process(payload.model_dump_json().encode()) is None
