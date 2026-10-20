from sqlalchemy import Column, ForeignKey, Table

from fastapi_aisiki.db.base import Base

# N:N — um usuário pode ter vários perfis e um perfil pode ter vários usuários.
user_profiles = Table(
    "user_profiles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("profile_id", ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
)
