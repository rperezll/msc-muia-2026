from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SimulatorState(StrEnum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class SolarTelemetryPayload(BaseModel):
    """Payload de telemetría solar emitido por el simulador vía MQTT"""

    DATE_TIME: datetime = Field(
        ..., description="Timestamp de la lectura (auto-parseado desde ISO string)"
    )
    PLANT_ID: int = Field(..., description="ID de la planta solar")
    SOURCE_KEY: str = Field(..., description="Identificador único del inversor/placa")
    DC_POWER: float = Field(..., description="Potencia DC generada")
    AC_POWER: float = Field(..., description="Potencia AC generada")
    DAILY_YIELD: float = Field(..., description="Rendimiento diario")
    TOTAL_YIELD: float = Field(..., description="Rendimiento total acumulado")
    AMBIENT_TEMPERATURE: float = Field(..., description="Temperatura ambiente en Celsius")
    MODULE_TEMPERATURE: float = Field(..., description="Temperatura del módulo en Celsius")
    IRRADIATION: float = Field(..., description="Nivel de irradiación")
    PLANT: int = Field(..., description="Número de referencia de la planta")
