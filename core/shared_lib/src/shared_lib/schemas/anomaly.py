from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from shared_lib.schemas.telemetry import SolarTelemetryPayload
from shared_lib.utils import new_id, now_utc


class AnomalyClassification(StrEnum):
    POWER_DEGRADATION = "power_degradation"
    THERMAL_STRESS = "thermal_stress"
    IRRADIATION_MISMATCH = "irradiation_mismatch"
    DC_SIDE_FAULT = "dc_side_fault"
    INVERTER_FAULT = "inverter_fault"
    GRID_INSTABILITY = "grid_instability"
    NIGHT_RESIDUAL_POWER = "night_residual_power"
    SENSOR_FAULT = "sensor_fault"
    UNKNOWN = "unknown"


class AnomalyDetection(BaseModel):
    """Detección individual de anomalía en un inversor"""

    detection_id: str = Field(default_factory=new_id)
    source_key: str
    timestamp: datetime
    mae: float | None = None
    threshold: float | None = None
    payload: SolarTelemetryPayload


class AnomalyReport(BaseModel):
    """Lote de detecciones de un mismo inversor, publicado en RabbitMQ y MQTT"""

    report_id: str = Field(default_factory=new_id)
    source_key: str
    detections: list[AnomalyDetection]
    created_at: datetime = Field(default_factory=now_utc)
