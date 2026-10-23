import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_aisiki.core.exceptions import AppError, ConflictError, NotFoundError
from fastapi_aisiki.models import User
from fastapi_aisiki.repositories.profile import ProfileRepository
from fastapi_aisiki.repositories.user import UserRepository
from fastapi_aisiki.schemas.user import UserAdminUpdate, UserUpdateMe


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.profiles = ProfileRepository(session)

    async def get(self, user_id: uuid.UUID) -> User:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        return user

    async def list(self, *, offset: int, limit: int) -> tuple[Sequence[User], int]:
        return await self.users.list(offset=offset, limit=limit)

    async def update_me(self, user: User, data: UserUpdateMe) -> User:
        changes = data.model_dump(exclude_unset=True, exclude_none=True)
        new_email = changes.get("email", user.email)
        if new_email != user.email and await self.users.get_by_email(new_email):
            raise ConflictError("E-mail já cadastrado.")
        for field, value in changes.items():
            setattr(user, field, value)
        await self.session.commit()
        return user

    async def admin_update(self, user_id: uuid.UUID, data: UserAdminUpdate) -> User:
        user = await self.get(user_id)
        for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(user, field, value)
        await self.session.commit()
        return user

    async def delete(self, user_id: uuid.UUID, *, requested_by: User) -> None:
        if user_id == requested_by.id:
            raise AppError("Você não pode excluir a si mesmo.")
        user = await self.get(user_id)
        await self.users.delete(user)
        await self.session.commit()

    async def add_profile(self, user_id: uuid.UUID, profile_id: uuid.UUID) -> User:
        user = await self.get(user_id)
        profile = await self.profiles.get(profile_id)
        if profile is None:
            raise NotFoundError("Perfil não encontrado.")
        if profile not in user.profiles:
            user.profiles.append(profile)
            await self.session.commit()
        return user

    async def remove_profile(self, user_id: uuid.UUID, profile_id: uuid.UUID) -> User:
        user = await self.get(user_id)
        profile = next((p for p in user.profiles if p.id == profile_id), None)
        if profile is None:
            raise NotFoundError("Usuário não possui este perfil.")
        user.profiles.remove(profile)
        await self.session.commit()
        return user
