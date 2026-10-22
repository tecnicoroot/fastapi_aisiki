import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from pwdlib import PasswordHash

from fastapi_aisiki.core.config import settings

TokenType = Literal["access", "refresh"]

_password_hash = PasswordHash.recommended()  # Argon2id

# Hash usado para equalizar o tempo de resposta quando o usuário não existe
# (mitiga enumeração de e-mails por timing attack).
DUMMY_PASSWORD_HASH = _password_hash.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)


def create_token(subject: str, token_type: TokenType, token_version: int) -> str:
    now = datetime.now(UTC)
    if token_type == "access":  # noqa: S105
        expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "ver": token_version,
        "iat": now,
        "exp": expires_at,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(
        payload, settings.SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica e valida o JWT. Lança ``jwt.PyJWTError`` se inválido/expirado."""
    return jwt.decode(
        token,
        settings.SECRET_KEY.get_secret_value(),
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub", "type"]},
    )


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_reset_token() -> tuple[str, str]:
    """Retorna (token_bruto, hash). Apenas o hash é persistido no banco."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)
