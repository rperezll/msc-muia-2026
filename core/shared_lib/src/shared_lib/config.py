from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class LlmProvider(StrEnum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    RUNPOD = "runpod"


class EngineMode(StrEnum):
    RLM = "rlm"
    SINGLE_PASS = "single_pass"


def _find_core_root() -> Path:
    """Busca la raíz de core/ subiendo hasta encontrar config.yml"""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "config.yml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("No se encontró config.yml en ningún directorio padre")


CORE_ROOT = _find_core_root()
REPO_ROOT = CORE_ROOT.parent
CONFIG_FILE_PATH = CORE_ROOT / "config.yml"

KERAS_DIR = REPO_ROOT / "models" / "keras"


def keras_plant_dir(plant_id: int) -> Path:
    return KERAS_DIR / f"plant_{plant_id}"


class MqttServiceConfig(BaseModel):
    host: str = "localhost"
    port: int = 1883


class RabbitMQServiceConfig(BaseModel):
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"


class ServicesConfig(BaseModel):
    mqtt: MqttServiceConfig = Field(default_factory=MqttServiceConfig)
    rabbitmq: RabbitMQServiceConfig = Field(default_factory=RabbitMQServiceConfig)


class SimulatorConfig(BaseModel):
    csv_file_path: str
    # Pausa entre instantes de muestreo distintos (simula el intervalo real de 15 min)
    publish_delay: float = Field(default=2.0, gt=0.0)
    # Pausa entre mensajes del mismo instante
    burst_delay: float = Field(default=0.1, ge=0.0)


class DetectorConfig(BaseModel):
    anomaly_buffer_max: int = Field(default=10, ge=1)
    lstm_threshold_key: str = "robust_threshold"


class ExplainerConfig(BaseModel):
    engine_mode: EngineMode = EngineMode.RLM
    llm_provider: LlmProvider
    api_key: str | None = None
    target_model: str
    base_url: str | None = None
    runpod_url: str | None = None
    max_iterations: int = Field(default=10, ge=1)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class McpServerConfig(BaseModel):
    name: str
    embedder_provider: LlmProvider = LlmProvider.OLLAMA
    embedder_model: str = "nomic-embed-text"
    embedder_api_key: str | None = None
    embedder_base_url: str | None = None
    lancedb_path: str = "data/lancedb"
    rag_top_k: int = Field(default=5, ge=1)
    host: str = "localhost"
    port: int = 8000
    chunk_size: int = Field(default=512, ge=1)
    chunk_overlap: int = Field(default=64, ge=0)


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class AppConfig(BaseModel):
    log_level: LogLevel = "INFO"
    log_levels: dict[str, LogLevel] = Field(default_factory=dict)
    services: ServicesConfig
    simulator: SimulatorConfig
    detector: DetectorConfig
    explainer: ExplainerConfig
    mcp_servers: list[McpServerConfig]


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Lee el YAML, lo parsea y devuelve el modelo validado"""
    if not CONFIG_FILE_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración en: {CONFIG_FILE_PATH}"
        )

    with open(CONFIG_FILE_PATH, encoding="utf-8") as f:
        config_dict = yaml.safe_load(f) or {}

    return AppConfig(**config_dict)


config = get_config()
