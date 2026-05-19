from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from shared_lib.logger import get_logger

if TYPE_CHECKING:
    from shared_lib.config import MqttServiceConfig

log = get_logger("mqtt")

MessageCallback = Callable[[str, bytes], None]
ConnectCallback = Callable[[], None]


class MqttTransport:
    """Wrapper sobre paho-mqtt desacoplado de topics y payloads concretos"""

    def __init__(self, client_id: str, mqtt_config: MqttServiceConfig) -> None:
        self._config = mqtt_config
        self._client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )

        self._subscriptions: dict[str, MessageCallback] = {}
        self._on_connect_cb: ConnectCallback | None = None

        self._client.on_connect = self._handle_connect
        self._client.on_message = self._handle_message

    def on_connect(self, callback: ConnectCallback) -> None:
        """Registra un callback que se ejecuta cada vez que se conecta"""
        self._on_connect_cb = callback

    def subscribe(self, topic: str, callback: MessageCallback) -> None:
        """Suscribe a topic y enruta los mensajes entrantes a callback"""
        self._subscriptions[topic] = callback
        if self._client.is_connected():
            self._client.subscribe(topic)

    def publish(
        self,
        topic: str,
        payload: str | bytes,
        *,
        retain: bool = False,
    ) -> None:
        """Publica payload en el topic"""
        self._client.publish(topic, payload, retain=retain)

    def connect(self) -> None:
        """Conecta al broker y arranca el loop de red en segundo plano"""
        self._client.connect(self._config.host, self._config.port)
        self._client.loop_start()

    def disconnect(self) -> None:
        """Detiene el loop de red y desconecta del broker"""
        self._client.loop_stop()
        self._client.disconnect()
        log.info("Desconectado del broker MQTT.")

    def _handle_connect(self, client, userdata, flags, rc, properties=None) -> None:
        log.info(
            "Conectado al broker MQTT (%s:%d)",
            self._config.host,
            self._config.port,
        )
        # Resuscribir tras reconexión
        for topic in self._subscriptions:
            self._client.subscribe(topic)
            log.debug("Suscrito a: %s", topic)

        if self._on_connect_cb:
            self._on_connect_cb()

    def _handle_message(self, client, userdata, msg: mqtt.MQTTMessage) -> None:
        callback = self._subscriptions.get(msg.topic)
        if callback:
            callback(msg.topic, msg.payload)
        else:
            log.warning("Mensaje en topic sin handler registrado: %s", msg.topic)
