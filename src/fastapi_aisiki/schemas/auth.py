from typing import Literal

from pydantic import BaseModel

from fastapi_aisiki.schemas.user import NormalizedEmail, Password


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: NormalizedEmail


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: Password


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: Password
