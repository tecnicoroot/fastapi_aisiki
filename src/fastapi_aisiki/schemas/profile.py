import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

ProfileName = Annotated[str, Field(min_length=2, max_length=50, pattern=r"^[a-z][a-z0-9_-]*$")]


class ProfileCreate(BaseModel):
    name: ProfileName
    description: str | None = Field(None, max_length=255)


class ProfileUpdate(BaseModel):
    name: ProfileName | None = None
    description: str | None = Field(None, max_length=255)


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
