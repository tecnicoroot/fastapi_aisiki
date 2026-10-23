import os

# Precisa vir ANTES de qualquer import da aplicação (settings é carregado no import).
os.environ["ENVIRONMENT"] = "test"
os.environ["POSTGRES_DB"] = os.environ.get("TEST_POSTGRES_DB", "app_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-com-pelo-menos-32-caracteres")

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from fastapi_aisiki import models  # noqa: F401
from fastapi_aisiki.api.deps import get_queue
from fastapi_aisiki.core.config import settings
from fastapi_aisiki.core.security import create_token, hash_password
from fastapi_aisiki.db.base import Base
from fastapi_aisiki.db.session import get_session
from fastapi_aisiki.main import app as fastapi_app
from fastapi_aisiki.models import Profile, User

DEFAULT_PASSWORD = "Senha@12345"


class FakeQueue:
    """Substitui o Redis/ARQ nos testes, registrando os jobs enfileirados."""

    def __init__(self) -> None:
        self.jobs: list[tuple[str, dict[str, Any]]] = []

    async def enqueue(self, function: str, **kwargs: Any) -> None:
        self.jobs.append((function, kwargs))


async def _prepare_database() -> None:
    conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD.get_secret_value(),
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", settings.POSTGRES_DB
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{settings.POSTGRES_DB}"')
    finally:
        await conn.close()

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _setup_database() -> None:
    asyncio.run(_prepare_database())


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Cada teste roda dentro de uma transação revertida ao final (isolamento total)."""
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        session.add_all([Profile(name="admin"), Profile(name="user")])
        await session.flush()
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def fake_queue() -> FakeQueue:
    return FakeQueue()


@pytest.fixture
async def client(db_session: AsyncSession, fake_queue: FakeQueue) -> AsyncIterator[AsyncClient]:
    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    fastapi_app.dependency_overrides[get_session] = _override_session
    fastapi_app.dependency_overrides[get_queue] = lambda: fake_queue
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


UserFactory = Callable[..., Coroutine[Any, Any, User]]


@pytest.fixture
def user_factory(db_session: AsyncSession) -> UserFactory:
    counter = {"n": 0}

    async def _create(
        *, email: str | None = None, is_superuser: bool = False, profiles: list[str] | None = None
    ) -> User:
        counter["n"] += 1
        result = await db_session.execute(select(Profile).where(Profile.name.in_(profiles or [])))
        profile_objs = list(result.scalars().all())
        user = User(
            email=email or f"user{counter['n']}@example.com",
            full_name=f"Usuário {counter['n']}",
            hashed_password=hash_password(DEFAULT_PASSWORD),
            is_superuser=is_superuser,
            profiles=profile_objs,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    return _create


def auth_headers(user: User) -> dict[str, str]:
    token = create_token(str(user.id), "access", user.token_version)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user(user_factory: UserFactory) -> User:
    return await user_factory(profiles=["user"])


@pytest.fixture
async def superuser(user_factory: UserFactory) -> User:
    return await user_factory(email="admin@example.com", is_superuser=True)
