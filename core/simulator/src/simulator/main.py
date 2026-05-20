import signal

from shared_lib.config import config
from shared_lib.messaging import MqttTransport

from ._controller import SimulatorController
from ._reader import CsvTelemetryReader
from ._simulator import Simulator


def main() -> None:
    transport = MqttTransport(client_id="simulator", mqtt_config=config.services.mqtt)
    reader = CsvTelemetryReader()
    controller = SimulatorController(transport)
    sim = Simulator(reader, controller, transport, config.simulator)

    signal.signal(signal.SIGINT, lambda s, f: sim.shutdown())
    signal.signal(signal.SIGTERM, lambda s, f: sim.shutdown())

    sim.run()


if __name__ == "__main__":
    main()
