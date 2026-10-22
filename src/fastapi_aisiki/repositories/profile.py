import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, profile_id: uuid.UUID) -> Profile | None:
        return await self.session.get(Profile, profile_id)

    async def get_by_name(self, name: str) -> Profile | None:
        result = await self.session.execute(select(Profile).where(Profile.name == name))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[Profile], int]:
        total = await self.session.scalar(select(func.count()).select_from(Profile)) or 0
        result = await self.session.execute(
            select(Profile).order_by(Profile.name).offset(offset).limit(limit)
        )
        return result.scalars().all(), total

    def add(self, profile: Profile) -> None:
        self.session.add(profile)

    async def delete(self, profile: Profile) -> None:
        await self.session.delete(profile)
