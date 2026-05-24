from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path

CORE_DIR = Path(__file__).parent.resolve()
_DETECTOR_WAIT_S = 8


def _log(msg: str) -> None:
    print(f"[pipeline] {msg}", flush=True)


def _start(name: str) -> subprocess.Popen[bytes]:
    proc = subprocess.Popen(["uv", "run", name], cwd=CORE_DIR)
    _log(f"{name} iniciado (PID={proc.pid})")
    return proc


def _shutdown(procs: list[subprocess.Popen[bytes]]) -> None:
    _log("Apagando procesos...")
    for p in reversed(procs):
        if p.poll() is None:
            p.terminate()
    for p in reversed(procs):
        try:
            p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()


def main() -> None:
    # 1. Detector
    detector = _start("detector")

    _log(f"Esperando {_DETECTOR_WAIT_S}s para que el detector cargue modelos y conecte MQTT...")
    for _ in range(_DETECTOR_WAIT_S):
        time.sleep(1)
        if detector.poll() is not None:
            _log(f"ERROR: detector terminó inesperadamente (rc={detector.returncode})")
            sys.exit(1)

    # 2. Explainer
    explainer = _start("explainer")

    # 3. Simulator
    simulator = _start("simulator")

    def _handler(sig: int, frame: object) -> None:
        _shutdown([detector, explainer, simulator])
        sys.exit(0)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

    _log("Pipeline en marcha. Ctrl+C para detener.")
    rc = simulator.wait()
    _log(f"Simulator terminó (rc={rc})")

    _shutdown([detector, explainer])
    _log("Pipeline finalizado")


if __name__ == "__main__":
    main()
