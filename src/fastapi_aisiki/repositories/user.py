import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[User], int]:
        total = await self.session.scalar(select(func.count()).select_from(User)) or 0
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return result.scalars().all(), total

    def add(self, user: User) -> None:
        self.session.add(user)

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
