import time

from shared_lib.config import CORE_ROOT, SimulatorConfig
from shared_lib.logger import get_logger
from shared_lib.messaging import MQTT_TOPIC_TELEMETRY, MqttTransport
from shared_lib.schemas import SolarTelemetryPayload

from ._controller import SimulatorController
from ._reader import CsvTelemetryReader

log = get_logger("simulator")


class Simulator:
    """Orquesta la lectura del CSV, el estado y la publicación de telemetría"""

    def __init__(
        self,
        reader: CsvTelemetryReader,
        controller: SimulatorController,
        transport: MqttTransport,
        cfg: SimulatorConfig,
    ) -> None:
        self._reader = reader
        self._controller = controller
        self._transport = transport
        self._cfg = cfg
        self._rows: list[SolarTelemetryPayload] = []
        self._position = 0
        self._running = True

    def run(self) -> None:
        self._rows = self._reader.load(CORE_ROOT / self._cfg.csv_file_path)
        log.info("CSV cargado: %d filas", len(self._rows))

        self._transport.connect()
        log.info("Simulador arrancado en estado 'stopped' esperando 'play'")

        try:
            self._loop()
        finally:
            self._shutdown()

    def shutdown(self) -> None:
        self._running = False
        self._controller.release()

    def _loop(self) -> None:
        while self._running:
            self._controller.wait_for_play(timeout=0.5)

            if not self._running:
                break
            if not self._controller.is_playing:
                continue

            if self._controller.consume_position_reset():
                self._position = 0

            if self._position >= len(self._rows):
                self._controller.mark_completed()
                continue

            payload = self._rows[self._position]
            self._publish(payload)
            log.debug("Publicada fila %d/%d", self._position + 1, len(self._rows))
            self._position += 1

            time.sleep(self._next_delay(self._position, payload))

    def _publish(self, payload: SolarTelemetryPayload) -> None:
        self._transport.publish(MQTT_TOPIC_TELEMETRY, payload.model_dump_json())

    def _next_delay(self, next_pos: int, current: SolarTelemetryPayload) -> float:
        """Delay corto entre inversores del mismo instante y mayor entre instantes distintos"""
        next_is_same_timestamp = (
            next_pos < len(self._rows) and self._rows[next_pos].DATE_TIME == current.DATE_TIME
        )
        return self._cfg.burst_delay if next_is_same_timestamp else self._cfg.publish_delay

    def _shutdown(self) -> None:
        log.info("Cerrando simulador...")
        self._controller.mark_completed()
        self._transport.disconnect()
        log.info("Simulador desconectado.")
