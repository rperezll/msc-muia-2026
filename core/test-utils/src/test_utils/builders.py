from datetime import datetime

from shared_lib.schemas import SolarTelemetryPayload

_TELEMETRY_DEFAULTS: dict = {
    "DATE_TIME": datetime(2020, 6, 1, 0, 0),
    "PLANT_ID": 1,
    "SOURCE_KEY": "TEST_INV",
    "DC_POWER": 100.0,
    "AC_POWER": 95.0,
    "DAILY_YIELD": 500.0,
    "TOTAL_YIELD": 10000.0,
    "AMBIENT_TEMPERATURE": 25.0,
    "MODULE_TEMPERATURE": 30.0,
    "IRRADIATION": 0.5,
    "PLANT": 1,
}


def make_telemetry_payload(**overrides) -> SolarTelemetryPayload:
    return SolarTelemetryPayload(**(_TELEMETRY_DEFAULTS | overrides))
