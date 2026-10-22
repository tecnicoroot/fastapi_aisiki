"""Configuração do worker. Execute com: arq app.worker.settings.WorkerSettings"""

import logging
from typing import Any, ClassVar

from fastapi_aisiki.core.logging import setup_logging
from fastapi_aisiki.core.queue import get_redis_settings
from fastapi_aisiki.worker.tasks import send_password_reset_email, send_welcome_email

logger = logging.getLogger(__name__)


async def startup(_: dict[str, Any]) -> None:
    setup_logging()
    logger.info("Worker iniciado.")


async def shutdown(_: dict[str, Any]) -> None:
    logger.info("Worker finalizado.")


class WorkerSettings:
    functions: ClassVar = [send_welcome_email, send_password_reset_email]
    redis_settings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_tries = 5
    job_timeout = 60
