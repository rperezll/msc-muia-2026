import json

from shared_lib.config import CORE_ROOT, AppConfig, get_config


def generate_schema() -> None:
    """Genera el JSON Schema a partir del modelo Pydantic de AppConfig"""
    schema_path = CORE_ROOT / "config.schema.json"

    schema = AppConfig.model_json_schema()

    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Esquema generado en: {schema_path}")


if __name__ == "__main__":
    generate_schema()

    try:
        print("Validando configuración desde YAML...")
        conf = get_config()
        print(f"Nivel de log: {conf.log_level}")
        print("Configuración validada correctamente.")
    except Exception as e:
        print(f"Error de validación en config.yml:\n{e}")
        exit(1)
