from __future__ import annotations

import atexit
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

CORE_DIR = Path(__file__).parent.resolve()
_DETECTOR_WAIT_S = 8
_IS_WINDOWS = platform.system() == "Windows"


def _log(msg: str) -> None:
    print(f"[pipeline] {msg}", flush=True)


def _start(name: str) -> subprocess.Popen[bytes]:
    proc = subprocess.Popen(["uv", "run", name], cwd=CORE_DIR)
    _log(f"{name} iniciado (PID={proc.pid})")
    return proc


def _kill(proc: subprocess.Popen[bytes]) -> None:
    """Para finalizar procesos con seguridad en windows"""
    if proc.poll() is not None:
        return
    if _IS_WINDOWS:
        subprocess.call(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def _shutdown(procs: list[subprocess.Popen[bytes]]) -> None:
    _log("Apagando procesos...")
    for p in reversed(procs):
        _kill(p)


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

    # 3. Knowledge API (HTTP, no depende de MQTT/RabbitMQ)
    knowledge = _start("knowledge")

    # 4. Simulator
    simulator = _start("simulator")

    procs = [detector, explainer, knowledge, simulator]

    # atexit garantiza limpieza aunque el padre muera sin Ctrl+C
    atexit.register(_shutdown, procs)

    def _handler(sig: int, frame: object) -> None:
        sys.exit(0)  # dispara atexit

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

    _log("Pipeline en marcha. Ctrl+C para detener.")
    rc = simulator.wait()
    _log(f"Simulator terminó (rc={rc})")

    _shutdown([detector, explainer, knowledge])
    _log("Pipeline finalizado")


if __name__ == "__main__":
    main()
