import json

import pytest

from explainer.audit.logger import AuditLogger
from explainer.audit.record import AuditRecord
from explainer.engines.engine import ExplainerEngine, _tokens_per_second
from shared_lib.config import ExplainerConfig
from test_utils.builders import make_anomaly_report

from .conftest import FakeLLM


def _make_engine(tmp_path, llm: FakeLLM) -> ExplainerEngine:
    """Instancia ExplainerEngine sin __init__ para inyectar deps sin tocar config"""
    engine = ExplainerEngine.__new__(ExplainerEngine)
    engine._cfg = ExplainerConfig(
        llm_provider="openai",
        target_model="m",
        api_key="sk-test",
        temperature=0.3,
        audit_path=str(tmp_path / "audit.jsonl"),
    )
    engine._llm = llm
    engine._audit = AuditLogger(path=str(tmp_path / "audit.jsonl"))
    return engine


class TestTokensPerSecond:
    def test_normal(self):
        assert _tokens_per_second(100, 2000) == 50.0

    def test_completion_tokens_none(self):
        assert _tokens_per_second(None, 2000) is None

    def test_completion_tokens_cero(self):
        assert _tokens_per_second(0, 2000) is None

    def test_llm_ms_cero(self):
        assert _tokens_per_second(100, 0) is None

    def test_redondeo_a_un_decimal(self):
        assert _tokens_per_second(10, 3000) == 3.3


class TestExplainerEngineRun:
    def test_exito_devuelve_json_valido(self, tmp_path):
        report = make_anomaly_report()
        engine = _make_engine(tmp_path, FakeLLM())
        resultado = engine.run("query", context=report.model_dump_json())
        incidentes = json.loads(resultado)
        assert isinstance(incidentes, list)
        assert len(incidentes) == 1

    def test_exito_instance_id_igual_source_key(self, tmp_path):
        report = make_anomaly_report(source_key="INV_99")
        engine = _make_engine(tmp_path, FakeLLM())
        resultado = engine.run("query", context=report.model_dump_json())
        incidente = json.loads(resultado)[0]
        assert incidente["event_metadata"]["instance_id"] == "INV_99"

    def test_exito_anomaly_type_del_analisis(self, tmp_path):
        report = make_anomaly_report()
        engine = _make_engine(tmp_path, FakeLLM())
        resultado = engine.run("query", context=report.model_dump_json())
        incidente = json.loads(resultado)[0]
        assert incidente["rag_search_parameters"]["anomaly_type"] == "power_degradation"

    def test_exito_tres_rag_queries(self, tmp_path):
        report = make_anomaly_report()
        engine = _make_engine(tmp_path, FakeLLM())
        resultado = engine.run("query", context=report.model_dump_json())
        incidente = json.loads(resultado)[0]
        assert len(incidente["suggested_rag_search_queries"]) == 3

    def test_exito_escribe_audit_ok(self, tmp_path):
        report = make_anomaly_report()
        engine = _make_engine(tmp_path, FakeLLM())
        engine.run("query", context=report.model_dump_json())
        lineas = (tmp_path / "audit.jsonl").read_text().strip().splitlines()
        assert len(lineas) == 1
        rec = AuditRecord.model_validate_json(lineas[0])
        assert rec.status == "ok"
        assert rec.prompt_chars > 0

    def test_on_progress_invocado_dos_veces(self, tmp_path):
        report = make_anomaly_report()
        engine = _make_engine(tmp_path, FakeLLM())
        llamadas: list[tuple[int, int]] = []
        engine.run(
            "query",
            context=report.model_dump_json(),
            on_progress=lambda i, m: llamadas.append((i, m)),
        )
        assert llamadas == [(1, 2), (2, 2)]

    def test_error_llm_propaga_excepcion(self, tmp_path):
        report = make_anomaly_report()
        engine = _make_engine(tmp_path, FakeLLM(raises=ValueError("boom")))
        with pytest.raises(ValueError, match="boom"):
            engine.run("query", context=report.model_dump_json())

    def test_error_llm_escribe_audit_error(self, tmp_path):
        report = make_anomaly_report()
        engine = _make_engine(tmp_path, FakeLLM(raises=ValueError("boom")))
        with pytest.raises(ValueError):
            engine.run("query", context=report.model_dump_json())
        lineas = (tmp_path / "audit.jsonl").read_text().strip().splitlines()
        assert len(lineas) == 1
        rec = AuditRecord.model_validate_json(lineas[0])
        assert rec.status == "error"
        assert rec.error_type == "ValueError"
