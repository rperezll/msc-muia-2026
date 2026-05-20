import threading

from shared_lib.logger import get_logger
from shared_lib.messaging import (
    MQTT_TOPIC_SIMULATOR_CONTROL,
    MQTT_TOPIC_SIMULATOR_STATUS,
    MqttTransport,
)
from shared_lib.schemas import SimulatorState

log = get_logger("simulator")

_TRANSITIONS: dict[str, dict[SimulatorState, SimulatorState]] = {
    "play": {
        SimulatorState.STOPPED: SimulatorState.PLAYING,
        SimulatorState.PAUSED: SimulatorState.PLAYING,
    },
    "pause": {
        SimulatorState.PLAYING: SimulatorState.PAUSED,
    },
    "stop": {
        SimulatorState.PLAYING: SimulatorState.STOPPED,
        SimulatorState.PAUSED: SimulatorState.STOPPED,
    },
}


class SimulatorController:
    """Gestiona el estado del simulador y los mensajes MQTT de control/status"""

    def __init__(self, transport: MqttTransport) -> None:
        self._transport = transport
        self._state = SimulatorState.STOPPED
        self._lock = threading.Lock()
        self._play_event = threading.Event()
        # Señaliza al loop que debe reiniciar la posición a 0
        self._position_reset = threading.Event()

        transport.on_connect(self._on_connect)
        transport.subscribe(MQTT_TOPIC_SIMULATOR_CONTROL, self._on_command)

    @property
    def state(self) -> SimulatorState:
        return self._state

    def wait_for_play(self, timeout: float) -> None:
        self._play_event.wait(timeout=timeout)

    @property
    def is_playing(self) -> bool:
        return self._play_event.is_set()

    def mark_completed(self) -> None:
        """Invocado cuando se agota el CSV"""
        with self._lock:
            self._state = SimulatorState.STOPPED
            self._play_event.clear()
        log.info("⏹️ CSV completado. Simulador detenido.")
        self._publish_status()

    def consume_position_reset(self) -> bool:
        """Devuelve True una sola vez si hay un reset de posición pendiente"""
        if self._position_reset.is_set():
            self._position_reset.clear()
            return True
        return False

    def release(self) -> None:
        """Desbloquea wait_for_play para que el loop pueda salir."""
        self._play_event.set()

    def _on_connect(self) -> None:
        log.info("Suscrito a topic de control: %s", MQTT_TOPIC_SIMULATOR_CONTROL)
        self._publish_status()

    def _on_command(self, _topic: str, payload: bytes) -> None:
        command = payload.decode("utf-8").strip().lower()
        log.info("Comando recibido: '%s'", command)

        with self._lock:
            next_state = _TRANSITIONS.get(command, {}).get(self._state)
            if next_state is None:
                log.warning("Comando '%s' ignorado (estado actual: %s)", command, self._state)
                return

            prev_state = self._state
            self._state = next_state
            self._update_play_event(command, prev_state)

        log.info("Estado → %s", self._state)
        self._publish_status()

    def _update_play_event(self, command: str, prev_state: SimulatorState) -> None:
        if command == "play":
            self._play_event.set()
            if prev_state == SimulatorState.STOPPED:
                self._position_reset.set()
        elif command == "stop":
            self._play_event.clear()
            self._position_reset.set()
        elif command == "pause":
            self._play_event.clear()

    def _publish_status(self) -> None:
        self._transport.publish(MQTT_TOPIC_SIMULATOR_STATUS, self._state, retain=True)
