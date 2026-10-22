import uuid

from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, ProfileServiceDep
from app.models import Profile
from app.schemas.common import Page, PageQuery
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=Page[ProfileRead])
async def list_profiles(
    _: CurrentUser, service: ProfileServiceDep, params: PageQuery
) -> Page[ProfileRead]:
    items, total = await service.list(offset=params.offset, limit=params.size)
    return Page[ProfileRead](
        items=[ProfileRead.model_validate(p) for p in items],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get("/{profile_id}", response_model=ProfileRead)
async def get_profile(profile_id: uuid.UUID, _: CurrentUser, service: ProfileServiceDep) -> Profile:
    return await service.get(profile_id)


@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(data: ProfileCreate, _: AdminUser, service: ProfileServiceDep) -> Profile:
    return await service.create(data)


@router.patch("/{profile_id}", response_model=ProfileRead)
async def update_profile(
    profile_id: uuid.UUID, data: ProfileUpdate, _: AdminUser, service: ProfileServiceDep
) -> Profile:
    return await service.update(profile_id, data)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: uuid.UUID, _: AdminUser, service: ProfileServiceDep) -> None:
    await service.delete(profile_id)
