from datetime import datetime

from shared_lib.schemas import SolarTelemetryPayload
from shared_lib.schemas.anomaly import AnomalyDetection, AnomalyReport

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


def make_detection(
    *, source_key="TEST_INV", mae=0.9, threshold=0.5, timestamp=None, **payload_overrides
) -> AnomalyDetection:
    ts = timestamp or datetime(2020, 6, 1, 12, 0)
    return AnomalyDetection(
        source_key=source_key,
        timestamp=ts,
        mae=mae,
        threshold=threshold,
        payload=make_telemetry_payload(SOURCE_KEY=source_key, **payload_overrides),
    )


def make_anomaly_report(*, source_key="TEST_INV", detections=None) -> AnomalyReport:
    return AnomalyReport(
        source_key=source_key,
        detections=detections or [make_detection(source_key=source_key)],
    )
