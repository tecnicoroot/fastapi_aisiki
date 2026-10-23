"""Cria perfis padrão e o superusuário inicial (idempotente)."""

import asyncio
import logging

from fastapi_aisiki.core.config import settings
from fastapi_aisiki.core.logging import setup_logging
from fastapi_aisiki.core.security import hash_password
from fastapi_aisiki.db.session import SessionLocal, engine
from fastapi_aisiki.models import Profile, User
from fastapi_aisiki.repositories.profile import ProfileRepository
from fastapi_aisiki.repositories.user import UserRepository

logger = logging.getLogger(__name__)

DEFAULT_PROFILES = {
    "admin": "Administrador do sistema",
    "user": "Usuário padrão",
}


async def seed() -> None:
    async with SessionLocal() as session:
        profiles_repo = ProfileRepository(session)
        users_repo = UserRepository(session)

        profiles: dict[str, Profile] = {}
        for name, description in DEFAULT_PROFILES.items():
            profile = await profiles_repo.get_by_name(name)
            if profile is None:
                profile = Profile(name=name, description=description)
                profiles_repo.add(profile)
                logger.info("Perfil '%s' criado.", name)
            profiles[name] = profile

        if await users_repo.get_by_email(settings.FIRST_SUPERUSER_EMAIL) is None:
            users_repo.add(
                User(
                    email=settings.FIRST_SUPERUSER_EMAIL.lower(),
                    full_name="Administrador",
                    hashed_password=hash_password(
                        settings.FIRST_SUPERUSER_PASSWORD.get_secret_value()
                    ),
                    is_superuser=True,
                    profiles=[profiles["admin"], profiles["user"]],
                )
            )
            logger.info("Superusuário '%s' criado.", settings.FIRST_SUPERUSER_EMAIL)

        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    setup_logging()
    asyncio.run(seed())
