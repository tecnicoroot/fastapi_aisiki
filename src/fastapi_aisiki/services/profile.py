import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_aisiki.core.exceptions import ConflictError, NotFoundError
from fastapi_aisiki.models import Profile
from fastapi_aisiki.repositories.profile import ProfileRepository
from fastapi_aisiki.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profiles = ProfileRepository(session)

    async def get(self, profile_id: uuid.UUID) -> Profile:
        profile = await self.profiles.get(profile_id)
        if profile is None:
            raise NotFoundError("Perfil não encontrado.")
        return profile

    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[Profile], int]:
        return await self.profiles.list(offset=offset, limit=limit)

    async def create(self, data: ProfileCreate) -> Profile:
        if await self.profiles.get_by_name(data.name):
            raise ConflictError("Já existe um perfil com este nome.")
        profile = Profile(name=data.name, description=data.description)
        self.profiles.add(profile)
        await self.session.commit()
        return profile

    async def update(self, profile_id: uuid.UUID, data: ProfileUpdate) -> Profile:
        profile = await self.get(profile_id)
        changes = data.model_dump(exclude_unset=True)
        new_name = changes.get("name", profile.name)
        if new_name != profile.name and (
            new_name is None or await self.profiles.get_by_name(new_name)
        ):
            raise ConflictError("Já existe um perfil com este nome.")
        for field, value in changes.items():
            setattr(profile, field, value)
        await self.session.commit()
        return profile

    async def delete(self, profile_id: uuid.UUID) -> None:
        profile = await self.get(profile_id)
        await self.profiles.delete(profile)
        await self.session.commit()
