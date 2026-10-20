from sqlalchemy import String, false, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_aisiki.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from fastapi_aisiki.models.associations import user_profiles
from fastapi_aisiki.models.profile import Profile


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    is_superuser: Mapped[bool] = mapped_column(default=False, server_default=false())
    # Incrementado ao trocar/redefinir senha: invalida todos os JWT emitidos antes.
    token_version: Mapped[int] = mapped_column(default=0, server_default="0")

    profiles: Mapped[list[Profile]] = relationship(
        secondary=user_profiles, lazy="selectin", order_by=Profile.name
    )

    def has_any_profile(self, *names: str) -> bool:
        return any(p.name in names for p in self.profiles)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
