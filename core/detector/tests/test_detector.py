from __future__ import annotations

import json
from typing import TYPE_CHECKING

from detector._detector import Detector
from shared_lib.messaging import MQTT_TOPIC_DETECTOR_ANOMALY, MQTT_TOPIC_TELEMETRY
from shared_lib.schemas import AnomalyDetection, AnomalyReport
from test_utils.builders import make_telemetry_payload

if TYPE_CHECKING:
    from test_utils.fake_mqtt import FakeMqttTransport
    from test_utils.fake_rabbitmq import FakeRabbitMqTransport


class FakeProcessor:
    """Fake de TelemetryProcessor que devuelve un reporte configurable"""

    def __init__(self, report: AnomalyReport | None = None) -> None:
        self.report = report
        self.calls: list[bytes] = []

    def process(self, raw: bytes) -> AnomalyReport | None:
        self.calls.append(raw)
        return self.report


def _make_report() -> AnomalyReport:
    payload = make_telemetry_payload()
    detection = AnomalyDetection(
        source_key="TEST_INV",
        timestamp=payload.DATE_TIME,
        mae=0.9,
        threshold=0.5,
        payload=payload,
    )
    return AnomalyReport(source_key="TEST_INV", detections=[detection])


def _inject(transport: FakeMqttTransport, payload=None) -> None:
    p = payload or make_telemetry_payload()
    transport.simulate_message(MQTT_TOPIC_TELEMETRY, p.model_dump_json().encode())


class TestPublicacion:
    def test_publica_en_mqtt_cuando_hay_reporte(
        self, mqtt: FakeMqttTransport, rabbitmq: FakeRabbitMqTransport
    ):
        Detector(mqtt, rabbitmq, FakeProcessor(_make_report()))
        _inject(mqtt)
        anomaly = [p for t, p, *_ in mqtt.published if t == MQTT_TOPIC_DETECTOR_ANOMALY]
        assert len(anomaly) == 1

    def test_publica_en_rabbitmq_cuando_hay_reporte(
        self, mqtt: FakeMqttTransport, rabbitmq: FakeRabbitMqTransport
    ):
        Detector(mqtt, rabbitmq, FakeProcessor(_make_report()))
        _inject(mqtt)
        assert len(rabbitmq.published) == 1

    def test_sin_reporte_no_publica_nada(
        self, mqtt: FakeMqttTransport, rabbitmq: FakeRabbitMqTransport
    ):
        Detector(mqtt, rabbitmq, FakeProcessor(None))
        _inject(mqtt)
        anomaly = [p for t, p, *_ in mqtt.published if t == MQTT_TOPIC_DETECTOR_ANOMALY]
        assert len(anomaly) == 0
        assert len(rabbitmq.published) == 0

    def test_sin_rabbitmq_solo_publica_mqtt(self, mqtt: FakeMqttTransport):
        Detector(mqtt, None, FakeProcessor(_make_report()))
        _inject(mqtt)
        anomaly = [p for t, p, *_ in mqtt.published if t == MQTT_TOPIC_DETECTOR_ANOMALY]
        assert len(anomaly) == 1

    def test_payload_publicado_es_json_valido(
        self, mqtt: FakeMqttTransport, rabbitmq: FakeRabbitMqTransport
    ):
        Detector(mqtt, rabbitmq, FakeProcessor(_make_report()))
        _inject(mqtt)
        raw = next(p for t, p, *_ in mqtt.published if t == MQTT_TOPIC_DETECTOR_ANOMALY)
        parsed = json.loads(raw)
        assert parsed["source_key"] == "TEST_INV"
        assert len(parsed["detections"]) == 1

    def test_rabbitmq_y_mqtt_publican_el_mismo_payload(
        self, mqtt: FakeMqttTransport, rabbitmq: FakeRabbitMqTransport
    ):
        Detector(mqtt, rabbitmq, FakeProcessor(_make_report()))
        _inject(mqtt)
        mqtt_payload = next(p for t, p, *_ in mqtt.published if t == MQTT_TOPIC_DETECTOR_ANOMALY)
        assert rabbitmq.published[0] == mqtt_payload.encode()


class TestSuscripcion:
    def test_delega_mensaje_al_processor(self, mqtt: FakeMqttTransport):
        processor = FakeProcessor()
        Detector(mqtt, None, processor)
        _inject(mqtt)
        assert len(processor.calls) == 1

    def test_multiples_mensajes_delegan_al_processor(self, mqtt: FakeMqttTransport):
        processor = FakeProcessor()
        Detector(mqtt, None, processor)
        _inject(mqtt)
        _inject(mqtt)
        _inject(mqtt)
        assert len(processor.calls) == 3
