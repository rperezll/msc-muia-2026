import threading

import pytest

from shared_lib.schemas import SimulatorState, SolarTelemetryPayload
from test_utils.fake_mqtt import FakeMqttTransport


@pytest.fixture
def transport() -> FakeMqttTransport:
    return FakeMqttTransport()


class FakeController:
    """Fake de SimulatorController pero siempre en estado playing"""

    def __init__(self, *, start_playing: bool = True) -> None:
        self._event = threading.Event()
        self._completed = threading.Event()
        self._is_completed = False
        if start_playing:
            self._event.set()

    @property
    def state(self) -> SimulatorState:
        return SimulatorState.PLAYING if self._event.is_set() else SimulatorState.STOPPED

    @property
    def is_playing(self) -> bool:
        return self._event.is_set() and not self._is_completed

    def wait_for_play(self, timeout: float) -> None:
        self._event.wait(timeout=timeout)

    def consume_position_reset(self) -> bool:
        return False

    def mark_completed(self) -> None:
        self._is_completed = True
        self._event.clear()
        self._completed.set()

    def release(self) -> None:
        self._event.set()

    def wait_completed(self, timeout: float = 2.0) -> bool:
        return self._completed.wait(timeout=timeout)


class FakeReader:
    """Fake de CsvTelemetryReader que devuelve una lista fija de payloads"""

    def __init__(self, rows: list[SolarTelemetryPayload]) -> None:
        self._rows = rows

    def load(self, path) -> list[SolarTelemetryPayload]:
        return self._rows
