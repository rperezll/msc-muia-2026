from shared_lib.messaging.rabbitmq import ConsumeCallback


class FakeRabbitMqTransport:
    """Fake de RabbitMqTransport para tests unitarios"""

    def __init__(self) -> None:
        self.published: list[bytes] = []
        self._consumer: ConsumeCallback | None = None

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    @property
    def is_connected(self) -> bool:
        return True

    def publish(self, payload: str | bytes) -> None:
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
        self.published.append(body)

    def consume(self, callback: ConsumeCallback, prefetch: int = 1) -> None:
        self._consumer = callback

    def stop_consuming(self) -> None:
        pass

    def simulate_message(self, payload: bytes) -> None:
        """Entrega un mensaje al consumer registrado"""
        if self._consumer:
            self._consumer(payload)
