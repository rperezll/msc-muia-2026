from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import psycopg

from shared_lib.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterator

    from shared_lib.config import PostgresConfig

log = get_logger("postgres")


class PostgresTransport:
    """Wrapper para psycopg"""

    def __init__(self, postgres_config: PostgresConfig) -> None:
        self._config = postgres_config
        self._connection: psycopg.Connection | None = None

    def connect(self) -> None:
        """Abre la conexión a Postgres"""
        self._connection = psycopg.connect(
            host=self._config.host,
            port=self._config.port,
            user=self._config.user,
            password=self._config.password,
            dbname=self._config.database,
        )
        log.info(
            "Conectado a Postgres (%s:%d), base '%s'",
            self._config.host,
            self._config.port,
            self._config.database,
        )

    def disconnect(self) -> None:
        """Cierra la conexión de forma segura"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            log.info("Desconectado de Postgres.")

    @property
    def is_connected(self) -> bool:
        return self._connection is not None and not self._connection.closed

    def _ensure_connected(self) -> None:
        """Reconecta si la conexión se ha perdido"""
        if not self.is_connected:
            log.warning("Conexión Postgres perdida, reconectando...")
            self.connect()

    @contextmanager
    def cursor(self) -> Iterator[psycopg.Cursor]:
        """Operación transaccional + commit/rollback. Reintenta una vez si la conexión está zombi."""
        for attempt in range(2):
            self._ensure_connected()
            assert self._connection is not None
            try:
                with self._connection.cursor() as cur:
                    try:
                        yield cur
                        self._connection.commit()
                        return
                    except Exception:
                        self._connection.rollback()
                        raise
            except psycopg.OperationalError:
                if attempt == 0:
                    log.warning("Conexión Postgres caída detectada, reconectando...")
                    self._connection = None
                    continue
                raise
