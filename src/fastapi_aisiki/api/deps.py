from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import PermissionDeniedError
from app.core.queue import TaskQueue
from app.db.session import get_session
from app.models import User
from app.services.auth import AuthService
from app.services.profile import ProfileService
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_queue(request: Request) -> TaskQueue:
    queue: TaskQueue = request.app.state.queue
    return queue


QueueDep = Annotated[TaskQueue, Depends(get_queue)]


# ------------------------------------------------------------------ serviços
def get_auth_service(session: SessionDep, queue: QueueDep) -> AuthService:
    return AuthService(session, queue)


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


def get_profile_service(session: SessionDep) -> ProfileService:
    return ProfileService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


# ------------------------------------------------------------------ autenticação
async def get_current_user(token: TokenDep, auth: AuthServiceDep) -> User:
    return await auth.get_user_from_token(token, expected_type="access")


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_profiles(*names: str) -> Callable[[User], Awaitable[User]]:
    """Exige que o usuário tenha ao menos um dos perfis (superusuário sempre passa)."""

    async def _checker(user: CurrentUser) -> User:
        if user.is_superuser or user.has_any_profile(*names):
            return user
        raise PermissionDeniedError

    return _checker


AdminUser = Annotated[User, Depends(require_profiles("admin"))]
