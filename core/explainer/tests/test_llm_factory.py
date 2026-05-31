from types import SimpleNamespace

import pytest

from explainer.llm._llm_factory import create_llm
from explainer.llm.ollama import Ollama
from explainer.llm.openai import OpenAI
from explainer.llm.runpod import Runpod
from shared_lib.config import ExplainerConfig


class TestCreateLlm:
    def test_openai_devuelve_instancia_openai(self):
        cfg = ExplainerConfig(llm_provider="openai", target_model="gpt-4", api_key="sk-test")
        llm = create_llm(cfg)
        assert isinstance(llm, OpenAI)

    def test_ollama_devuelve_instancia_ollama(self):
        cfg = ExplainerConfig(llm_provider="ollama", target_model="llama3")
        llm = create_llm(cfg)
        assert isinstance(llm, Ollama)

    def test_runpod_con_url_devuelve_instancia_runpod(self):
        cfg = ExplainerConfig(
            llm_provider="runpod",
            target_model="llama3",
            runpod_url="http://runpod.example.com",
        )
        llm = create_llm(cfg)
        assert isinstance(llm, Runpod)

    def test_runpod_sin_url_lanza_value_error(self):
        cfg = ExplainerConfig(llm_provider="runpod", target_model="llama3", runpod_url=None)
        with pytest.raises(ValueError, match="runpod_url"):
            create_llm(cfg)

    def test_proveedor_no_soportado_lanza_value_error(self):
        cfg_falso = SimpleNamespace(
            llm_provider=SimpleNamespace(value="xxx"),
            target_model="m",
            api_key=None,
            base_url=None,
            runpod_url=None,
        )
        with pytest.raises(ValueError, match="xxx"):
            create_llm(cfg_falso)
