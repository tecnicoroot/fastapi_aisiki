"""Importa todos os models para registrá-los no metadata (necessário ao Alembic)."""

from fastapi_aisiki.models.associations import user_profiles
from fastapi_aisiki.models.password_reset import PasswordResetToken
from fastapi_aisiki.models.profile import Profile
from fastapi_aisiki.models.user import User

__all__ = ["PasswordResetToken", "Profile", "User", "user_profiles"]
