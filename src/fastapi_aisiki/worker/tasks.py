"""Tarefas executadas de forma assíncrona pelo worker ARQ (fila no Redis)."""

import logging
from typing import Any

import aiosmtplib
from arq import Retry

from fastapi_aisiki.core.config import settings
from fastapi_aisiki.services.email import send_email

logger = logging.getLogger(__name__)


async def send_welcome_email(ctx: dict[str, Any], email: str, full_name: str) -> None:
    try:
        await send_email(
            to=email,
            subject=f"Bem-vindo(a) ao {settings.PROJECT_NAME}!",
            text=f"Olá, {full_name}! Sua conta foi criada com sucesso.",
            html=f"<p>Olá, <strong>{full_name}</strong>! Sua conta foi criada com sucesso.</p>",
        )
    except aiosmtplib.SMTPException as exc:
        raise Retry(defer=ctx["job_try"] * 10) from exc
    logger.info("E-mail de boas-vindas enviado para %s", email)


async def send_password_reset_email(ctx: dict[str, Any], email: str, reset_url: str) -> None:
    minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    try:
        await send_email(
            to=email,
            subject="Recuperação de senha",
            text=(
                f"Recebemos uma solicitação para redefinir sua senha.\n"
                f"Acesse: {reset_url}\n\nO link expira em {minutes} minutos. "
                "Se não foi você, ignore este e-mail."
            ),
            html=(
                "<p>Recebemos uma solicitação para redefinir sua senha.</p>"
                f'<p><a href="{reset_url}">Clique aqui para redefinir</a></p>'
                f"<p>O link expira em {minutes} minutos. Se não foi você, ignore este e-mail.</p>"
            ),
        )
    except aiosmtplib.SMTPException as exc:
        raise Retry(defer=ctx["job_try"] * 10) from exc
    logger.info("E-mail de recuperação de senha enviado para %s", email)
