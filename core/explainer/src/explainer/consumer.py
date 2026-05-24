import threading
import time
from datetime import datetime
from uuid import uuid4

from shared_lib.config import config
from shared_lib.logger import get_logger
from shared_lib.messaging.mqtt import MqttTransport
from shared_lib.messaging.rabbitmq import RabbitMqTransport
from shared_lib.messaging.topics import (
    MQTT_TOPIC_JOB_EVENT,
    RABBITMQ_QUEUE_ANOMALIES,
    RABBITMQ_QUEUE_JOB_EVENTS,
)
from shared_lib.schemas.anomaly import AnomalyReport
from shared_lib.schemas.jobs import JobEvent, JobEventType

from .engines import create_engine
from .prompts import QUERY_RLM, QUERY_SINGLE_PASS

log = get_logger("explainer")

WORKER_ID = f"explainer-worker-{uuid4().hex[:8]}"

_busy = threading.Event()


def _make_job_transport() -> RabbitMqTransport:
    transport = RabbitMqTransport(
        queue=RABBITMQ_QUEUE_JOB_EVENTS,
        rabbitmq_config=config.services.rabbitmq,
    )
    transport.connect()
    return transport


def _publish_job_event(transport: RabbitMqTransport, event: JobEvent) -> None:
    try:
        transport.publish(event.model_dump_json())
    except Exception as e:
        log.error("Error publicando JobEvent (%s): %s", event.type, e)


def _notify_mqtt(mqtt_transport: MqttTransport, event: JobEvent) -> None:
    """Emite por MQTT los eventos de COMPLETED / FAILED)"""
    try:
        mqtt_transport.publish(MQTT_TOPIC_JOB_EVENT, event.model_dump_json())
    except Exception as e:
        log.error("Error publicando JobEvent en MQTT (%s): %s", event.type, e)


def _handle_report(
    body: bytes, job_transport: RabbitMqTransport, mqtt_transport: MqttTransport
) -> None:
    report = AnomalyReport.model_validate_json(body)

    if _busy.is_set():
        log.warning("[%s] Trabajo en curso, descartando reporte %s", WORKER_ID, report.report_id)
        return

    _busy.set()
    started_at = datetime.now()

    _publish_job_event(
        job_transport,
        JobEvent(
            type=JobEventType.STARTED,
            report_id=report.report_id,
            source_key=report.source_key,
            started_at=started_at,
        ),
    )

    def on_progress(iteration: int, max_iterations: int) -> None:
        _publish_job_event(
            job_transport,
            JobEvent(
                type=JobEventType.PROGRESS,
                report_id=report.report_id,
                source_key=report.source_key,
                iteration=iteration,
                max_iterations=max_iterations,
            ),
        )

    try:
        log.info(
            "[%s] Procesando reporte %s (%d anomalías, inversor=%s)",
            WORKER_ID,
            report.report_id,
            len(report.detections),
            report.source_key,
        )
        engine = create_engine(config.explainer)
        query = QUERY_RLM if config.explainer.engine_mode.value == "rlm" else QUERY_SINGLE_PASS
        result = engine.run(query, context=report.model_dump_json(), on_progress=on_progress)

        duration_ms = int((time.time() - started_at.timestamp()) * 1000)
        completed = JobEvent(
            type=JobEventType.COMPLETED,
            report_id=report.report_id,
            source_key=report.source_key,
            result=result,
            duration_ms=duration_ms,
            report=report,
        )
        _publish_job_event(job_transport, completed)
        _notify_mqtt(mqtt_transport, completed)
        log.info("[%s] Reporte %s completado: %s", WORKER_ID, report.report_id, str(result)[:200])

    except Exception as e:
        duration_ms = int((time.time() - started_at.timestamp()) * 1000)
        failed = JobEvent(
            type=JobEventType.FAILED,
            report_id=report.report_id,
            source_key=report.source_key,
            error=str(e),
            duration_ms=duration_ms,
        )
        _publish_job_event(job_transport, failed)
        _notify_mqtt(mqtt_transport, failed)
        raise

    finally:
        _busy.clear()


def start_consumer() -> None:
    log.info("Iniciando explainer con worker_id=%s", WORKER_ID)

    job_transport = _make_job_transport()

    mqtt_transport = MqttTransport(
        client_id=f"explainer-{WORKER_ID}",
        mqtt_config=config.services.mqtt,
    )
    mqtt_transport.connect()

    anomaly_transport = RabbitMqTransport(
        queue=RABBITMQ_QUEUE_ANOMALIES,
        rabbitmq_config=config.services.rabbitmq,
    )
    anomaly_transport.connect()
    anomaly_transport.consume(lambda body: _handle_report(body, job_transport, mqtt_transport))
