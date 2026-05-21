from __future__ import annotations

import time
from typing import TYPE_CHECKING

from shared_lib.logger import get_logger
from shared_lib.messaging import (
    MQTT_TOPIC_DETECTOR_ANOMALY,
    MQTT_TOPIC_TELEMETRY,
    MqttTransport,
    RabbitMqTransport,
)

if TYPE_CHECKING:
    from ._processor import TelemetryProcessor

log = get_logger("detector")


class Detector:
    """Orquesta la conexión MQTT, el procesamiento y la publicación de reportes en RabbitMQ"""

    def __init__(
        self,
        mqtt: MqttTransport,
        rabbitmq: RabbitMqTransport | None,
        processor: TelemetryProcessor,
    ) -> None:
        self._mqtt = mqtt
        self._rabbitmq = rabbitmq
        self._processor = processor
        self._running = True

        self._mqtt.on_connect(self._on_connect)
        self._mqtt.subscribe(MQTT_TOPIC_TELEMETRY, self._on_telemetry)

    def run(self) -> None:
        self._mqtt.connect()
        log.info("Detector arrancado. Esperando telemetría en %s", MQTT_TOPIC_TELEMETRY)
        try:
            while self._running:
                time.sleep(0.5)
        finally:
            self._shutdown()

    def shutdown(self) -> None:
        self._running = False

    def _on_connect(self) -> None:
        log.info("Suscrito a topic de telemetría: %s", MQTT_TOPIC_TELEMETRY)

    def _on_telemetry(self, _topic: str, raw: bytes) -> None:
        report = self._processor.process(raw)
        if report:
            self._publish(
                report.model_dump_json(),
                report.source_key,
                len(report.detections),
                report.report_id,
            )

    def _publish(
        self, payload_json: str, source_key: str, n_detections: int, report_id: str
    ) -> None:
        self._mqtt.publish(MQTT_TOPIC_DETECTOR_ANOMALY, payload_json)
        log.info(
            "Reporte publicado en MQTT | inversor=%s | detecciones=%d", source_key, n_detections
        )

        if self._rabbitmq:
            try:
                self._rabbitmq.publish(payload_json)
                log.info("Reporte encolado en RabbitMQ | report_id=%s", report_id)
            except Exception:
                log.exception("Error publicando en RabbitMQ")
        else:
            log.warning("RabbitMQ no disponible, reporte solo emitido por MQTT")

    def _shutdown(self) -> None:
        log.info("Cerrando detector...")
        self._mqtt.disconnect()
        if self._rabbitmq:
            self._rabbitmq.disconnect()
        log.info("Detector desconectado.")
