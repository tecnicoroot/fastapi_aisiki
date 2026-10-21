from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field


class Message(BaseModel):
    message: str


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


PageQuery = Annotated[PageParams, Query()]
