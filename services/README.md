# msc-muia-2026 - Services

## Ejecución

```bash
docker compose up -d
```

## Purgar colas de RabbitMQ

Para limpiar mensajes residuales de ejecuciones anteriores:

```bash
docker exec rabbitmq_broker rabbitmqctl purge_queue anomalies
```
