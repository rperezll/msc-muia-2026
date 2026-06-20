# msc-muia-2026 - Core

> **Importante:** Es necesario levantar la infraestructura previamente para trabajar con los proyectos de `core/`. Ejecuta `docker compose -f compose.infra.yml up -d` en la raíz del repositorio.

> Todas las instrucciones siguientes se realizan sobre `core/`

```bash
uv sync
```

## Esquemas

Genera `config.schema.json` por primera vez para validar `config.yml`:

```bash
uv run generate-schema
```

## Simulador

```bash
uv run simulator
```

Arranca en `stopped` por defecto. Necesita un comando de `play` para comenzar a emitir (topic: `simulator/control`):

```bash
docker exec mqtt_broker mosquitto_pub -t simulator/control -m play
docker exec mqtt_broker mosquitto_pub -t simulator/control -m pause
docker exec mqtt_broker mosquitto_pub -t simulator/control -m stop
```

## Detector

```bash
uv run detector
```

Requiere los artefactos entrenados en `models/keras/plant_{1,2}/` (`config_solar.json`, `model_lstm_solar.keras`, `model_mlp_head.keras`, `scaler_solar.pkl`).

Consume telemetría de `telemetry/solar`, publica reportes de anomalía en `detector/anomaly` (MQTT) y los encola en RabbitMQ (`anomalies`) para que el explainer los procese.

## Explainer

```bash
uv run explainer
```

Consume anomalías de RabbitMQ (`anomalies`), genera la explicación con el LLM configurado y la persiste en Postgres.

## Knowledge

```bash
uv run knowledge
```

Servicio de recuperación (RAG) sobre la base vectorial. Expone su API en el `host`/`port` del bloque `knowledge` de `config.yml`.

## Tests

```bash
uv run --package simulator pytest simulator/tests/ -v
uv run --package detector pytest detector/tests/ -v
uv run --package explainer pytest explainer/tests/ -v
uv run --package knowledge pytest knowledge/tests/ -v
```

## Pipeline completo

Arranca todos los servicios del core a la vez:

```bash
uv run run_pipeline.py
```
