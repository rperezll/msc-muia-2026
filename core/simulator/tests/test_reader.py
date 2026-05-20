from pathlib import Path

import pytest

from simulator._reader import CsvTelemetryReader

_CSV_HEADER = (
    "DATE_TIME,PLANT_ID,SOURCE_KEY,DC_POWER,AC_POWER,"
    "DAILY_YIELD,TOTAL_YIELD,AMBIENT_TEMPERATURE,MODULE_TEMPERATURE,IRRADIATION,PLANT\n"
)


def _write_csv(path: Path, rows: list[str]) -> Path:
    path.write_text(_CSV_HEADER + "\n".join(rows), encoding="utf-8")
    return path


def _row(date_time: str, plant_id: str, source_key: str) -> str:
    return f"{date_time},{plant_id},{source_key},100,95,500,10000,25,30,0.5,1"


def test_normaliza_plant_id_kaggle_a_pipeline(tmp_path):
    csv = _write_csv(
        tmp_path / "data.csv",
        [
            _row("2020-06-01 00:00:00", "4135001", "INV1"),
            _row("2020-06-01 00:00:00", "4136001", "INV2"),
        ],
    )

    rows = CsvTelemetryReader().load(csv)

    assert rows[0].PLANT_ID == 1
    assert rows[1].PLANT_ID == 2


def test_plant_id_desconocido_se_conserva(tmp_path):
    csv = _write_csv(tmp_path / "data.csv", [_row("2020-06-01 00:00:00", "9999999", "INV1")])

    rows = CsvTelemetryReader().load(csv)

    assert rows[0].PLANT_ID == 9999999


def test_ordena_por_timestamp_y_source_key(tmp_path):
    # CSV desordenado y caótico
    csv = _write_csv(
        tmp_path / "data.csv",
        [
            _row("2020-06-01 00:15:00", "4135001", "INV_A"),
            _row("2020-06-01 00:00:00", "4135001", "INV_Z"),
            _row("2020-06-01 00:00:00", "4135001", "INV_A"),
        ],
    )

    rows = CsvTelemetryReader().load(csv)

    assert rows[0].SOURCE_KEY == "INV_A"
    assert rows[0].DATE_TIME.minute == 0
    assert rows[1].SOURCE_KEY == "INV_Z"
    assert rows[2].DATE_TIME.minute == 15


def test_lanza_error_si_csv_no_existe():
    with pytest.raises(FileNotFoundError, match="CSV no encontrado"):
        CsvTelemetryReader().load(Path("/nonexistent/data.csv"))


def test_devuelve_payloads_parseados(tmp_path):
    csv = _write_csv(tmp_path / "data.csv", [_row("2020-06-01 00:00:00", "4135001", "INV1")])

    rows = CsvTelemetryReader().load(csv)

    assert len(rows) == 1
    assert rows[0].DC_POWER == 100.0
    assert rows[0].SOURCE_KEY == "INV1"
