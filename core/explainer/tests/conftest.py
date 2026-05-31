from __future__ import annotations

import pytest

from shared_lib.schemas.anomaly import AnomalyClassification, LLMAnalysis
from test_utils.fake_mqtt import FakeMqttTransport
from test_utils.fake_rabbitmq import FakeRabbitMqTransport


class FakeLLM:
    """LLM mock que devuelve LLMAnalysis fijo o lanza excepción"""

    def __init__(self, *, raises: Exception | None = None) -> None:
        self._raises = raises
        self.received_messages: list[list[dict]] = []

    def chat_structured(self, messages, schema, **kwargs):
        self.received_messages.append(messages)
        if self._raises is not None:
            raise self._raises
        analysis = LLMAnalysis(
            anomaly_type=AnomalyClassification.POWER_DEGRADATION,
            affected_subsystem="DC/AC Conversion",
            summary="Test summary for unit tests.",
            suggested_rag_search_queries=["query 1", "query 2", "query 3"],
        )
        usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        return analysis, usage


@pytest.fixture
def mqtt() -> FakeMqttTransport:
    return FakeMqttTransport()


@pytest.fixture
def rabbitmq() -> FakeRabbitMqTransport:
    return FakeRabbitMqTransport()
