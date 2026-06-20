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

## Truncar tabla de explicaciones en PostgreSQL

```bash
docker exec -it postgres_db psql -U postgres -d muia -c "TRUNCATE TABLE explanations;"
```
