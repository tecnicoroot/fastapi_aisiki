import logging
import uuid
from datetime import timedelta
from urllib.parse import urlencode

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_aisiki.core.config import settings
from fastapi_aisiki.core.exceptions import AppError, AuthenticationError, ConflictError
from fastapi_aisiki.core.queue import TaskName, TaskQueue
from fastapi_aisiki.core.security import (
    DUMMY_PASSWORD_HASH,
    TokenType,
    create_token,
    decode_token,
    generate_reset_token,
    hash_password,
    hash_token,
    verify_password,
)
from fastapi_aisiki.db.base import utcnow
from fastapi_aisiki.models import PasswordResetToken, User
from fastapi_aisiki.repositories.password_reset import PasswordResetRepository
from fastapi_aisiki.repositories.profile import ProfileRepository
from fastapi_aisiki.repositories.user import UserRepository
from fastapi_aisiki.schemas.auth import TokenPair
from fastapi_aisiki.schemas.user import UserCreate

logger = logging.getLogger(__name__)

DEFAULT_PROFILE = "user"


class AuthService:
    def __init__(self, session: AsyncSession, queue: TaskQueue) -> None:
        self.session = session
        self.queue = queue
        self.users = UserRepository(session)
        self.profiles = ProfileRepository(session)
        self.reset_tokens = PasswordResetRepository(session)

    # ------------------------------------------------------------ cadastro
    async def register(self, data: UserCreate) -> User:
        if await self.users.get_by_email(data.email):
            raise ConflictError("E-mail já cadastrado.")

        default_profile = await self.profiles.get_by_name(DEFAULT_PROFILE)
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            profiles=[default_profile] if default_profile else [],
        )
        self.users.add(user)
        await self.session.commit()

        await self.queue.enqueue(
            TaskName.SEND_WELCOME_EMAIL, email=user.email, full_name=user.full_name
        )
        return user

    # ------------------------------------------------------------ login / tokens
    async def authenticate(self, email: str, password: str) -> TokenPair:
        user = await self.users.get_by_email(email)
        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)  # tempo constante
            raise AuthenticationError("E-mail ou senha incorretos.")
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("E-mail ou senha incorretos.")
        if not user.is_active:
            raise AuthenticationError("Usuário inativo.")
        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        user = await self.get_user_from_token(refresh_token, expected_type="refresh")
        return self._issue_tokens(user)

    async def get_user_from_token(self, token: str, expected_type: TokenType) -> User:
        try:
            payload = decode_token(token)
            user_id = uuid.UUID(payload["sub"])
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise AuthenticationError from exc

        if payload.get("type") != expected_type:
            raise AuthenticationError("Tipo de token inválido.")

        user = await self.users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError
        if payload.get("ver") != user.token_version:
            raise AuthenticationError("Token revogado.")
        return user

    @staticmethod
    def _issue_tokens(user: User) -> TokenPair:
        subject = str(user.id)
        return TokenPair(
            access_token=create_token(subject, "access", user.token_version),
            refresh_token=create_token(subject, "refresh", user.token_version),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------ senhas
    async def forgot_password(self, email: str) -> None:
        """Sempre retorna silenciosamente para não revelar se o e-mail existe."""
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active:
            logger.info("Recuperação de senha solicitada para e-mail inexistente/inativo.")
            return

        await self.reset_tokens.invalidate_all_for_user(user.id)
        raw_token, token_hash = generate_reset_token()
        self.reset_tokens.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=utcnow()
                + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
            )
        )
        await self.session.commit()

        reset_url = f"{settings.FRONTEND_URL}/reset-password?{urlencode({'token': raw_token})}"
        await self.queue.enqueue(
            TaskName.SEND_PASSWORD_RESET_EMAIL, email=user.email, reset_url=reset_url
        )

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        reset = await self.reset_tokens.get_valid_by_hash(hash_token(raw_token))
        if reset is None:
            raise AppError("Token inválido ou expirado.")
        user = await self.users.get(reset.user_id)
        if user is None or not user.is_active:
            raise AppError("Token inválido ou expirado.")

        await self.reset_tokens.invalidate_all_for_user(user.id)
        self._set_password(user, new_password)
        await self.session.commit()

    async def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.hashed_password):
            raise AppError("Senha atual incorreta.")
        self._set_password(user, new)
        await self.session.commit()

    @staticmethod
    def _set_password(user: User, new_password: str) -> None:
        user.hashed_password = hash_password(new_password)
        user.token_version += 1  # revoga todos os tokens anteriores
