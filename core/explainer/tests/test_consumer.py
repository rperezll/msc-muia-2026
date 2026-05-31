import json

import pytest

import explainer.consumer as consumer_mod
from explainer.consumer import _handle_report
from shared_lib.messaging.topics import MQTT_TOPIC_JOB_EVENT
from shared_lib.schemas.jobs import JobEvent, JobEventType
from test_utils.builders import make_anomaly_report
from test_utils.fake_mqtt import FakeMqttTransport
from test_utils.fake_rabbitmq import FakeRabbitMqTransport

_RESULT_JSON = json.dumps([{"event_metadata": {"instance_id": "TEST_INV"}}])


class FakeExplanationRepo:
    def __init__(self) -> None:
        self.saved: list[JobEvent] = []

    def save(self, event: JobEvent) -> None:
        self.saved.append(event)


@pytest.fixture(autouse=True)
def limpiar_busy():
    consumer_mod._busy.clear()
    yield
    consumer_mod._busy.clear()


class TestHandleReportHappyPath:
    def test_publica_started_y_completed_en_rabbitmq(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                return _RESULT_JSON

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        report = make_anomaly_report()
        job = FakeRabbitMqTransport()
        mqtt = FakeMqttTransport()
        repo = FakeExplanationRepo()

        _handle_report(report.model_dump_json().encode(), job, mqtt, repo)

        assert len(job.published) == 2
        ev0 = JobEvent.model_validate_json(job.published[0])
        ev1 = JobEvent.model_validate_json(job.published[1])
        assert ev0.type == JobEventType.STARTED
        assert ev1.type == JobEventType.COMPLETED

    def test_completed_en_mqtt(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                return _RESULT_JSON

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        report = make_anomaly_report()
        job = FakeRabbitMqTransport()
        mqtt = FakeMqttTransport()
        repo = FakeExplanationRepo()

        _handle_report(report.model_dump_json().encode(), job, mqtt, repo)

        assert len(mqtt.published) == 1
        topic, payload, _ = mqtt.published[0]
        assert topic == MQTT_TOPIC_JOB_EVENT
        ev = JobEvent.model_validate_json(payload)
        assert ev.type == JobEventType.COMPLETED

    def test_repo_save_llamado_una_vez(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                return _RESULT_JSON

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        report = make_anomaly_report()
        job = FakeRabbitMqTransport()
        mqtt = FakeMqttTransport()
        repo = FakeExplanationRepo()

        _handle_report(report.model_dump_json().encode(), job, mqtt, repo)

        assert len(repo.saved) == 1
        assert repo.saved[0].type == JobEventType.COMPLETED

    def test_busy_queda_limpio(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                return _RESULT_JSON

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        report = make_anomaly_report()
        _handle_report(
            report.model_dump_json().encode(),
            FakeRabbitMqTransport(),
            FakeMqttTransport(),
            FakeExplanationRepo(),
        )
        assert not consumer_mod._busy.is_set()


class TestHandleReportProgress:
    def test_publica_progress_en_rabbitmq(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                if on_progress:
                    on_progress(1, 2)
                    on_progress(2, 2)
                return _RESULT_JSON

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        report = make_anomaly_report()
        job = FakeRabbitMqTransport()

        _handle_report(
            report.model_dump_json().encode(),
            job,
            FakeMqttTransport(),
            FakeExplanationRepo(),
        )

        assert len(job.published) == 4
        ev1 = JobEvent.model_validate_json(job.published[1])
        ev2 = JobEvent.model_validate_json(job.published[2])
        assert ev1.type == JobEventType.PROGRESS
        assert ev1.iteration == 1
        assert ev1.max_iterations == 2
        assert ev2.type == JobEventType.PROGRESS
        assert ev2.iteration == 2


class TestHandleReportBusyGuard:
    def test_descarta_si_busy(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                return _RESULT_JSON

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        consumer_mod._busy.set()
        report = make_anomaly_report()
        job = FakeRabbitMqTransport()

        _handle_report(
            report.model_dump_json().encode(),
            job,
            FakeMqttTransport(),
            FakeExplanationRepo(),
        )

        assert len(job.published) == 0


class TestHandleReportFalloEngine:
    def test_publica_failed_y_propaga_excepcion(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                raise RuntimeError("engine explota")

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        report = make_anomaly_report()
        job = FakeRabbitMqTransport()
        mqtt = FakeMqttTransport()

        with pytest.raises(RuntimeError, match="engine explota"):
            _handle_report(
                report.model_dump_json().encode(),
                job,
                mqtt,
                FakeExplanationRepo(),
            )

        ev_rabbitmq = [JobEvent.model_validate_json(b) for b in job.published]
        tipos = [e.type for e in ev_rabbitmq]
        assert JobEventType.FAILED in tipos

        _, payload, _ = mqtt.published[0]
        ev_mqtt = JobEvent.model_validate_json(payload)
        assert ev_mqtt.type == JobEventType.FAILED

    def test_busy_se_limpia_tras_fallo(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                raise RuntimeError("fallo")

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)
        report = make_anomaly_report()

        with pytest.raises(RuntimeError):
            _handle_report(
                report.model_dump_json().encode(),
                FakeRabbitMqTransport(),
                FakeMqttTransport(),
                FakeExplanationRepo(),
            )

        assert not consumer_mod._busy.is_set()


class TestHandleReportFalloRepo:
    def test_completed_publicado_aunque_repo_falle(self, monkeypatch):
        class _Engine:
            def run(self, q, context=None, on_progress=None):
                return _RESULT_JSON

        monkeypatch.setattr("explainer.consumer.ExplainerEngine", _Engine)

        class _FailRepo:
            def save(self, event):
                raise Exception("postgres no disponible")

        report = make_anomaly_report()
        job = FakeRabbitMqTransport()
        mqtt = FakeMqttTransport()

        _handle_report(report.model_dump_json().encode(), job, mqtt, _FailRepo())

        ev = JobEvent.model_validate_json(job.published[-1])
        assert ev.type == JobEventType.COMPLETED
        assert len(mqtt.published) == 1
