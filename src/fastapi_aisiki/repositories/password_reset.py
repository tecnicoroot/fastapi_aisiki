import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_aisiki.db.base import utcnow
from fastapi_aisiki.models import PasswordResetToken


class PasswordResetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, token: PasswordResetToken) -> None:
        self.session.add(token)

    async def get_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > utcnow(),
            )
        )
        return result.scalar_one_or_none()

    async def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at.is_(None))
            .values(used_at=utcnow())
        )
