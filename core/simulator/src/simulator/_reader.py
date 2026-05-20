import csv
from pathlib import Path

from shared_lib.schemas import SolarTelemetryPayload

# El dataset de Kaggle usa IDs largos
# Los normalizamos a 1/2 para el pipeline
_PLANT_ID_MAP = {4135001: 1, 4136001: 2}
_TELEMETRY_FIELDS = set(SolarTelemetryPayload.model_fields.keys())


class CsvTelemetryReader:
    """Carga y normaliza el CSV de Kaggle a una lista ordenada de payloads"""

    def load(self, path: Path) -> list[SolarTelemetryPayload]:
        if not path.exists():
            raise FileNotFoundError(f"CSV no encontrado: {path}")

        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        # El CSV viene agrupado por inversor (SOURCE_KEY) y no cronológicamente
        # Ordenamos para emitir como lo haría un entorno real
        rows.sort(key=lambda r: (r["DATE_TIME"], r["SOURCE_KEY"]))

        return [self._parse_row(row) for row in rows]

    def _parse_row(self, row: dict[str, str]) -> SolarTelemetryPayload:
        filtered = {k: v for k, v in row.items() if k in _TELEMETRY_FIELDS}
        if "PLANT_ID" in filtered:
            raw_id = int(filtered["PLANT_ID"])
            filtered["PLANT_ID"] = _PLANT_ID_MAP.get(raw_id, raw_id)
        return SolarTelemetryPayload.model_validate(filtered)
