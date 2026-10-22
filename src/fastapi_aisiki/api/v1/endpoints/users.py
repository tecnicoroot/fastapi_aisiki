import uuid

from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, UserServiceDep
from app.models import User
from app.schemas.common import Page, PageQuery
from app.schemas.user import UserAdminUpdate, UserRead, UserUpdateMe

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdateMe, user: CurrentUser, service: UserServiceDep) -> User:
    return await service.update_me(user, data)


@router.get("", response_model=Page[UserRead])
async def list_users(_: AdminUser, service: UserServiceDep, params: PageQuery) -> Page[UserRead]:
    items, total = await service.list(offset=params.offset, limit=params.size)
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in items],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, _: AdminUser, service: UserServiceDep) -> User:
    return await service.get(user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID, data: UserAdminUpdate, _: AdminUser, service: UserServiceDep
) -> User:
    return await service.admin_update(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, admin: AdminUser, service: UserServiceDep) -> None:
    await service.delete(user_id, requested_by=admin)


@router.post("/{user_id}/profiles/{profile_id}", response_model=UserRead)
async def add_profile(
    user_id: uuid.UUID, profile_id: uuid.UUID, _: AdminUser, service: UserServiceDep
) -> User:
    return await service.add_profile(user_id, profile_id)


@router.delete("/{user_id}/profiles/{profile_id}", response_model=UserRead)
async def remove_profile(
    user_id: uuid.UUID, profile_id: uuid.UUID, _: AdminUser, service: UserServiceDep
) -> User:
    return await service.remove_profile(user_id, profile_id)
