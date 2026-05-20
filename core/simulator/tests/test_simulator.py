import threading

from shared_lib.config import SimulatorConfig
from shared_lib.messaging import MQTT_TOPIC_TELEMETRY
from simulator._simulator import Simulator
from test_utils.builders import make_telemetry_payload
from test_utils.fake_mqtt import FakeMqttTransport

from .conftest import FakeController, FakeReader


def _make_cfg() -> SimulatorConfig:
    return SimulatorConfig(csv_file_path="fake.csv", publish_delay=0.001, burst_delay=0.0)


def _run_until_complete(sim: Simulator, ctrl: FakeController, timeout: float = 3.0) -> None:
    """Arranca el simulador en un hilo y espera a que agote el CSV"""
    t = threading.Thread(target=sim.run, daemon=True)
    t.start()
    completed = ctrl.wait_completed(timeout=timeout)
    sim.shutdown()
    t.join(timeout=1.0)
    assert completed, "El simulador no completó el CSV en el tiempo esperado"


class TestPublicacion:
    def test_publica_todas_las_filas(self, transport: FakeMqttTransport):
        payloads = [make_telemetry_payload(), make_telemetry_payload()]
        ctrl = FakeController()
        sim = Simulator(FakeReader(payloads), ctrl, transport, _make_cfg())

        _run_until_complete(sim, ctrl)

        telemetry = [p for t, p, *_ in transport.published if t == MQTT_TOPIC_TELEMETRY]
        assert len(telemetry) == 2

    def test_csv_vacio_completa_sin_publicar(self, transport: FakeMqttTransport):
        ctrl = FakeController()
        sim = Simulator(FakeReader([]), ctrl, transport, _make_cfg())

        _run_until_complete(sim, ctrl)

        telemetry = [p for t, p, *_ in transport.published if t == MQTT_TOPIC_TELEMETRY]
        assert len(telemetry) == 0

    def test_payload_es_json_valido(self, transport: FakeMqttTransport):
        import json

        ctrl = FakeController()
        sim = Simulator(FakeReader([make_telemetry_payload()]), ctrl, transport, _make_cfg())

        _run_until_complete(sim, ctrl)

        raw = next(p for t, p, *_ in transport.published if t == MQTT_TOPIC_TELEMETRY)
        parsed = json.loads(raw)
        assert parsed["PLANT_ID"] == 1
        assert parsed["SOURCE_KEY"] == "TEST_INV"


class TestShutdown:
    def test_shutdown_detiene_el_loop(self, transport: FakeMqttTransport):
        # Simulador sin filas que queda bloqueado esperando play
        ctrl = FakeController(start_playing=False)
        sim = Simulator(FakeReader([]), ctrl, transport, _make_cfg())

        t = threading.Thread(target=sim.run, daemon=True)
        t.start()
        sim.shutdown()
        t.join(timeout=2.0)

        assert not t.is_alive()

    def test_llama_disconnect_al_cerrar(self, transport: FakeMqttTransport):
        disconnected = []
        transport.disconnect = lambda: disconnected.append(True)

        ctrl = FakeController()
        sim = Simulator(FakeReader([]), ctrl, transport, _make_cfg())

        _run_until_complete(sim, ctrl)

        assert disconnected


class TestDelay:
    def test_burst_delay_entre_inversores_del_mismo_instante(self):
        from datetime import datetime

        ts = datetime(2020, 6, 1, 0, 0)
        rows = [
            make_telemetry_payload(DATE_TIME=ts, SOURCE_KEY="INV_A"),
            make_telemetry_payload(DATE_TIME=ts, SOURCE_KEY="INV_B"),
            make_telemetry_payload(DATE_TIME=datetime(2020, 6, 1, 0, 15), SOURCE_KEY="INV_A"),
        ]
        cfg = _make_cfg()
        sim = Simulator(FakeReader(rows), FakeController(), FakeMqttTransport(), cfg)
        sim._rows = rows

        assert sim._next_delay(1, rows[0]) == cfg.burst_delay  # mismo timestamp
        assert sim._next_delay(2, rows[1]) == cfg.publish_delay  # timestamp distinto
