from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from test_utils.fake_mqtt import FakeMqttTransport
from test_utils.fake_rabbitmq import FakeRabbitMqTransport

if TYPE_CHECKING:
    import numpy as np


@pytest.fixture
def mqtt() -> FakeMqttTransport:
    return FakeMqttTransport()


@pytest.fixture
def rabbitmq() -> FakeRabbitMqTransport:
    return FakeRabbitMqTransport()


class FakeAnomalyDetector:
    """Fake de AnomalyDetector que evita cargar artefactos Keras/joblib en tests"""

    def __init__(
        self,
        *,
        features: list[str] | None = None,
        time_steps: int = 3,
        threshold: float = 0.5,
        returns_anomaly: bool = False,
        score: float = 0.0,
    ) -> None:
        self.features = features or ["IRRADIATION", "DC_POWER", "AC_POWER"]
        self.time_steps = time_steps
        self.threshold = threshold
        self._returns_anomaly = returns_anomaly
        self._score = score

    def predict(self, window: np.ndarray) -> tuple[float, bool]:
        return self._score, self._returns_anomaly
