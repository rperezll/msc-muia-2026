import pytest

from shared_lib.messaging import MQTT_TOPIC_SIMULATOR_CONTROL, MQTT_TOPIC_SIMULATOR_STATUS
from shared_lib.schemas import SimulatorState
from simulator._controller import SimulatorController
from test_utils.fake_mqtt import FakeMqttTransport


@pytest.fixture
def ctrl(transport: FakeMqttTransport) -> SimulatorController:
    controller = SimulatorController(transport)
    transport.connect()
    return controller


def _send(transport: FakeMqttTransport, command: str) -> None:
    transport.simulate_message(MQTT_TOPIC_SIMULATOR_CONTROL, command.encode())


def _last_status(transport: FakeMqttTransport) -> str:
    status_msgs = [p for t, p, _ in transport.published if t == MQTT_TOPIC_SIMULATOR_STATUS]
    return status_msgs[-1]


class TestTransiciones:
    def test_play_desde_stopped_activa_playing(self, transport, ctrl):
        _send(transport, "play")
        assert ctrl.state == SimulatorState.PLAYING
        assert ctrl.is_playing

    def test_play_desde_stopped_pide_reset_de_posicion(self, transport, ctrl):
        _send(transport, "play")
        assert ctrl.consume_position_reset()

    def test_consume_position_reset_es_de_un_solo_uso(self, transport, ctrl):
        _send(transport, "play")
        ctrl.consume_position_reset()
        assert not ctrl.consume_position_reset()

    def test_play_desde_paused_no_pide_reset_de_posicion(self, transport, ctrl):
        _send(transport, "play")
        _send(transport, "pause")
        ctrl.consume_position_reset()
        _send(transport, "play")
        assert not ctrl.consume_position_reset()

    def test_pause_desde_playing(self, transport, ctrl):
        _send(transport, "play")
        _send(transport, "pause")
        assert ctrl.state == SimulatorState.PAUSED
        assert not ctrl.is_playing

    def test_stop_desde_playing_pide_reset_de_posicion(self, transport, ctrl):
        _send(transport, "play")
        ctrl.consume_position_reset()
        _send(transport, "stop")
        assert ctrl.state == SimulatorState.STOPPED
        assert ctrl.consume_position_reset()

    def test_stop_desde_paused(self, transport, ctrl):
        _send(transport, "play")
        _send(transport, "pause")
        _send(transport, "stop")
        assert ctrl.state == SimulatorState.STOPPED

    def test_comando_invalido_ignorado(self, transport, ctrl):
        estado_previo = ctrl.state
        _send(transport, "rewind")
        assert ctrl.state == estado_previo

    def test_play_cuando_ya_esta_playing_ignorado(self, transport, ctrl):
        _send(transport, "play")
        published_antes = len(transport.published)
        _send(transport, "play")
        assert len(transport.published) == published_antes


class TestStatus:
    def test_publica_status_al_conectar(self, transport, ctrl):
        assert _last_status(transport) == SimulatorState.STOPPED

    def test_publica_status_al_cambiar_estado(self, transport, ctrl):
        _send(transport, "play")
        assert _last_status(transport) == SimulatorState.PLAYING

    def test_status_retain(self, transport, ctrl):
        retains = [r for t, _, r in transport.published if t == MQTT_TOPIC_SIMULATOR_STATUS]
        assert all(retains)


class TestMarkCompleted:
    def test_mark_completed_pasa_a_stopped(self, transport, ctrl):
        _send(transport, "play")
        ctrl.mark_completed()
        assert ctrl.state == SimulatorState.STOPPED
        assert not ctrl.is_playing

    def test_mark_completed_publica_status(self, transport, ctrl):
        _send(transport, "play")
        transport.published.clear()
        ctrl.mark_completed()
        assert _last_status(transport) == SimulatorState.STOPPED
