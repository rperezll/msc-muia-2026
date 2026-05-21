from __future__ import annotations

import signal

from shared_lib.config import config
from shared_lib.messaging import RABBITMQ_QUEUE_ANOMALIES, MqttTransport, RabbitMqTransport

from ._detector import Detector
from ._processor import TelemetryProcessor
from .inference import AnomalyDetector


def main() -> None:
    mqtt = MqttTransport(client_id="detector", mqtt_config=config.services.mqtt)

    rabbitmq: RabbitMqTransport | None = None
    try:
        rabbitmq = RabbitMqTransport(
            queue=RABBITMQ_QUEUE_ANOMALIES,
            rabbitmq_config=config.services.rabbitmq,
        )
        rabbitmq.connect()
    except Exception:
        from shared_lib.logger import get_logger

        get_logger("detector").warning("RabbitMQ no disponible")

    models = {
        pid: AnomalyDetector(plant_id=pid, threshold_key=config.detector.lstm_threshold_key)
        for pid in (1, 2)
    }
    processor = TelemetryProcessor(models, anomaly_buffer_max=config.detector.anomaly_buffer_max)
    detector = Detector(mqtt, rabbitmq, processor)

    signal.signal(signal.SIGINT, lambda s, f: detector.shutdown())
    signal.signal(signal.SIGTERM, lambda s, f: detector.shutdown())

    detector.run()


if __name__ == "__main__":
    main()
