from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from shared_lib.utils import MINUTES_IN_DAY

if TYPE_CHECKING:
    from shared_lib.schemas import SolarTelemetryPayload


def payload_to_feature_vector(
    payload: SolarTelemetryPayload,
    features: list[str],
) -> list[float]:
    """Extrae el vector de features del payload según la lista del modelo
    El TIME_SIN y TIME_COS se calculan a partir del timestamp
    """
    minute_of_day = payload.DATE_TIME.hour * 60 + payload.DATE_TIME.minute
    angle = 2 * math.pi * minute_of_day / MINUTES_IN_DAY

    computed = {
        "TIME_SIN": math.sin(angle),
        "TIME_COS": math.cos(angle),
    }

    vector: list[float] = []
    for f in features:
        if f in computed:
            vector.append(computed[f])
        else:
            vector.append(getattr(payload, f))
    return vector


class SlidingWindowBuffer:
    """Buffer de ventana deslizante por SOURCE_KEY para alimentar al LSTM"""

    def __init__(self, time_steps: int) -> None:
        self._time_steps = time_steps
        self._buffers: dict[str, list[list[float]]] = {}

    def push(self, source_key: str, vector: list[float]) -> np.ndarray | None:
        """Añade un vector al buffer del inversor"""
        buf = self._buffers.setdefault(source_key, [])
        buf.append(vector)

        if len(buf) < self._time_steps:
            return None

        if len(buf) > self._time_steps:
            buf.pop(0)

        return np.array(buf)
