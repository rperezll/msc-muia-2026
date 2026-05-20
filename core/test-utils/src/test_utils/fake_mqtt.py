from shared_lib.messaging.mqtt import ConnectCallback, MessageCallback


class FakeMqttTransport:
    """Fake de MqttTransport para tests unitarios"""

    def __init__(self) -> None:
        self.published: list[tuple[str, str | bytes, bool]] = []
        self._connect_cb: ConnectCallback | None = None
        self._subscriptions: dict[str, MessageCallback] = {}

    def on_connect(self, callback: ConnectCallback) -> None:
        self._connect_cb = callback

    def subscribe(self, topic: str, callback: MessageCallback) -> None:
        self._subscriptions[topic] = callback

    def publish(self, topic: str, payload: str | bytes, *, retain: bool = False) -> None:
        self.published.append((topic, payload, retain))

    def connect(self) -> None:
        if self._connect_cb:
            self._connect_cb()

    def disconnect(self) -> None:
        pass

    def simulate_message(self, topic: str, payload: bytes) -> None:
        """Inyecta un mensaje entrante como si viniera del broker"""
        cb = self._subscriptions.get(topic)
        if cb:
            cb(topic, payload)
