# msc-muia-2026 - Core

> Todas las instrucciones se realizan sobre `core/`

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

## Tests

```bash
uv run --package simulator pytest simulator/tests/ -v
uv run --package detector pytest detector/tests/ -v
```
