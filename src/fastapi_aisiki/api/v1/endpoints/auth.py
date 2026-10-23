from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_aisiki.api.deps import AuthServiceDep, CurrentUser
from fastapi_aisiki.models import User
from fastapi_aisiki.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
)
from fastapi_aisiki.schemas.common import Message
from fastapi_aisiki.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, auth: AuthServiceDep) -> User:
    return await auth.register(data)


@router.post("/login")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], auth: AuthServiceDep
) -> TokenPair:
    """Login OAuth2 (form-data). O campo ``username`` recebe o e-mail."""
    return await auth.authenticate(form.username, form.password)


@router.post("/refresh")
async def refresh(data: RefreshRequest, auth: AuthServiceDep) -> TokenPair:
    return await auth.refresh(data.refresh_token)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(data: ForgotPasswordRequest, auth: AuthServiceDep) -> Message:
    await auth.forgot_password(data.email)
    return Message(message="Se o e-mail estiver cadastrado, você receberá as instruções.")


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, auth: AuthServiceDep) -> Message:
    await auth.reset_password(data.token, data.new_password)
    return Message(message="Senha redefinida com sucesso.")


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest, user: CurrentUser, auth: AuthServiceDep
) -> Message:
    await auth.change_password(user, data.current_password, data.new_password)
    return Message(message="Senha alterada com sucesso.")
