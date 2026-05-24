from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pika

from shared_lib.logger import get_logger

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel

    from shared_lib.config import RabbitMQServiceConfig

log = get_logger("rabbitmq")

ConsumeCallback = Callable[[bytes], None]


class RabbitMqTransport:
    """Wrapper sobre pika desacoplado de colas y payloads concretos"""

    def __init__(self, queue: str, rabbitmq_config: RabbitMQServiceConfig) -> None:
        self._config = rabbitmq_config
        self._queue = queue
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def connect(self) -> None:
        """Abre conexión, declara la cola y obtiene el canal"""
        credentials = pika.PlainCredentials(self._config.user, self._config.password)
        params = pika.ConnectionParameters(
            host=self._config.host,
            port=self._config.port,
            credentials=credentials,
            heartbeat=0,
        )
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue=self._queue, durable=True)
        log.info(
            "Conectado a RabbitMQ (%s:%d), cola '%s'",
            self._config.host,
            self._config.port,
            self._queue,
        )

    def disconnect(self) -> None:
        """Cierra la conexión de forma segura"""
        if self._connection and self._connection.is_open:
            self._connection.close()
            log.info("Desconectado de RabbitMQ.")

    @property
    def is_connected(self) -> bool:
        return self._connection is not None and self._connection.is_open

    def _ensure_connected(self) -> None:
        """Reconecta si la conexión se ha perdido"""
        if not self.is_connected:
            log.warning("Conexión RabbitMQ perdida, reconectando...")
            self.connect()

    def publish(self, payload: str | bytes) -> None:
        """Publica el payload en la cola con persistencia"""
        self._ensure_connected()
        assert self._channel is not None
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        self._channel.basic_publish(
            exchange="",
            routing_key=self._queue,
            body=body,
            # Esto hace que los mensajes sean persistentes para ser resilientes a reruns
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def consume(self, callback: ConsumeCallback, prefetch: int = 1) -> None:
        """Recupera trabajos de la cola y hace ack si el callback no lanza excepción"""

        if not self._channel:
            raise RuntimeError("RabbitMqTransport no conectado. Llama a connect() primero.")

        self._channel.basic_qos(prefetch_count=prefetch)

        def _on_message(ch: BlockingChannel, method, _properties, body: bytes):
            try:
                callback(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                log.exception("Error procesando mensaje, requeue")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self._channel.basic_consume(queue=self._queue, on_message_callback=_on_message)
        log.info("Consumiendo de cola '%s'...", self._queue)
        self._channel.start_consuming()

    def stop_consuming(self) -> None:
        """Detiene el bucle de consume() de forma segura"""
        if self._channel and self._channel.is_open:
            self._channel.stop_consuming()
