from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_aisiki.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "profiles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"<Profile {self.name}>"
