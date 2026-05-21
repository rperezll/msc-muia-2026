from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shared_lib.logger import get_logger
from shared_lib.schemas import AnomalyDetection, AnomalyReport, SolarTelemetryPayload

from .preprocessing import SlidingWindowBuffer, payload_to_feature_vector

if TYPE_CHECKING:
    from .inference import AnomalyDetector

log = get_logger("detector")

_DEFAULT_PLANT_ID = 1  # Fallback cuando el payload no trae PLANT_ID reconocido (1 / 0)


class _AnomalyBuffer:
    """Acumula detecciones por SOURCE_KEY y hace flush al alcanzar el máximo"""

    def __init__(self, max_size: int) -> None:
        self._max = max_size
        self._buffers: dict[str, list[AnomalyDetection]] = {}

    def push(self, detection: AnomalyDetection) -> AnomalyReport | None:
        buf = self._buffers.setdefault(detection.source_key, [])
        buf.append(detection)
        if len(buf) >= self._max:
            return self._flush(detection.source_key)
        return None

    def flush(self, source_key: str) -> AnomalyReport | None:
        if self._buffers.get(source_key):
            return self._flush(source_key)
        return None

    def _flush(self, source_key: str) -> AnomalyReport:
        detections = self._buffers.pop(source_key)
        return AnomalyReport(source_key=source_key, detections=detections)


class TelemetryProcessor:
    """Procesa payloads de telemetría y devuelve reportes de anomalía"""

    def __init__(
        self,
        models: dict[int, AnomalyDetector],
        anomaly_buffer_max: int,
    ) -> None:
        time_steps = next(iter(models.values())).time_steps
        self._models = models
        self._window_buffer = SlidingWindowBuffer(time_steps)
        self._anomaly_buffer = _AnomalyBuffer(anomaly_buffer_max)

    def process(self, raw: bytes) -> AnomalyReport | None:
        """Parsea el mensaje MQTT y ejecuta el pipeline de detección"""
        try:
            payload = SolarTelemetryPayload.model_validate(json.loads(raw))
        except Exception:
            log.warning("Mensaje descartado: payload inválido")
            return None

        return self._run(payload)

    def _run(self, payload: SolarTelemetryPayload) -> AnomalyReport | None:
        model = self._resolve_model(payload.PLANT_ID)
        window_key = f"{payload.PLANT_ID}:{payload.SOURCE_KEY}"
        vector = payload_to_feature_vector(payload, model.features)
        window = self._window_buffer.push(window_key, vector)

        if window is None:
            return None

        mae, is_anomaly = model.predict(window)

        if is_anomaly:
            log.warning(
                "LSTM ANOMALÍA | plant_id=%d | inversor=%s | mae=%.6f | umbral=%.6f",
                payload.PLANT_ID,
                payload.SOURCE_KEY,
                mae,
                model.threshold,
            )
            detection = AnomalyDetection(
                source_key=payload.SOURCE_KEY,
                timestamp=payload.DATE_TIME,
                mae=round(mae, 6),
                threshold=model.threshold,
                payload=payload,
            )
            return self._anomaly_buffer.push(detection)

        log.info("LSTM OK | mae=%.6f | umbral=%.6f", mae, model.threshold)
        # Lectura normal tras anomalías (flush del buffer pendiente)
        return self._anomaly_buffer.flush(payload.SOURCE_KEY)

    def _resolve_model(self, plant_id: int) -> AnomalyDetector:
        model = self._models.get(plant_id)
        if model is not None:
            return model
        log.warning(
            "PLANT_ID desconocido (%s). Usando fallback plant_id=%d",
            plant_id,
            _DEFAULT_PLANT_ID,
        )
        return self._models[_DEFAULT_PLANT_ID]
