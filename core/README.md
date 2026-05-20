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

## Tests

```bash
uv run --package simulator pytest -v
```
