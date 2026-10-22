from typing import Any, Protocol

from arq.connections import ArqRedis, RedisSettings

from fastapi_aisiki.core.config import settings


class TaskName:
    """Nomes das tarefas registradas no worker (evita strings soltas)."""

    SEND_WELCOME_EMAIL = "send_welcome_email"
    SEND_PASSWORD_RESET_EMAIL = "send_password_reset_email"  # noqa: S105


class TaskQueue(Protocol):
    async def enqueue(self, function: str, **kwargs: Any) -> None: ...


class ArqTaskQueue:
    """Adaptador da fila ARQ (Redis) para o protocolo ``TaskQueue``."""

    def __init__(self, pool: ArqRedis) -> None:
        self._pool = pool

    async def enqueue(self, function: str, **kwargs: Any) -> None:
        await self._pool.enqueue_job(function, **kwargs)


def get_redis_settings() -> RedisSettings:
    return RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD.get_secret_value() if settings.REDIS_PASSWORD else None,
    )
