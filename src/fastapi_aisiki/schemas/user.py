import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from app.schemas.profile import ProfileRead

NormalizedEmail = Annotated[EmailStr, AfterValidator(lambda v: v.lower())]
Password = Annotated[str, Field(min_length=8, max_length=128)]
FullName = Annotated[str, Field(min_length=2, max_length=255)]


class UserCreate(BaseModel):
    email: NormalizedEmail
    full_name: FullName
    password: Password


class UserUpdateMe(BaseModel):
    full_name: FullName | None = None
    email: NormalizedEmail | None = None


class UserAdminUpdate(BaseModel):
    full_name: FullName | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    profiles: list[ProfileRead]
    created_at: datetime
