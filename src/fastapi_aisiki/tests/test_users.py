from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile, User
from tests.conftest import UserFactory, auth_headers

API = "/api/v1"


async def _profile_id(session: AsyncSession, name: str) -> str:
    profile = (await session.execute(select(Profile).where(Profile.name == name))).scalar_one()
    return str(profile.id)


async def test_regular_user_cannot_list_users(client: AsyncClient, user: User) -> None:
    response = await client.get(f"{API}/users", headers=auth_headers(user))
    assert response.status_code == 403


async def test_superuser_lists_users_paginated(
    client: AsyncClient, superuser: User, user_factory: UserFactory
) -> None:
    for _ in range(3):
        await user_factory()
    response = await client.get(f"{API}/users?page=1&size=2", headers=auth_headers(superuser))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    assert len(body["items"]) == 2


async def test_admin_profile_grants_access(client: AsyncClient, user_factory: UserFactory) -> None:
    admin = await user_factory(profiles=["admin"])
    response = await client.get(f"{API}/users", headers=auth_headers(admin))
    assert response.status_code == 200


async def test_user_can_have_multiple_profiles(
    client: AsyncClient, db_session: AsyncSession, superuser: User, user: User
) -> None:
    headers = auth_headers(superuser)
    response = await client.post(f"{API}/profiles", json={"name": "financeiro"}, headers=headers)
    finance_id = response.json()["id"]
    admin_id = await _profile_id(db_session, "admin")

    await client.post(f"{API}/users/{user.id}/profiles/{finance_id}", headers=headers)
    response = await client.post(f"{API}/users/{user.id}/profiles/{admin_id}", headers=headers)

    assert response.status_code == 200
    assert sorted(p["name"] for p in response.json()["profiles"]) == [
        "admin",
        "financeiro",
        "user",
    ]

    response = await client.delete(f"{API}/users/{user.id}/profiles/{admin_id}", headers=headers)
    assert sorted(p["name"] for p in response.json()["profiles"]) == ["financeiro", "user"]


async def test_add_nonexistent_profile(client: AsyncClient, superuser: User, user: User) -> None:
    response = await client.post(
        f"{API}/users/{user.id}/profiles/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(superuser),
    )
    assert response.status_code == 404


async def test_update_me(client: AsyncClient, user: User) -> None:
    response = await client.patch(
        f"{API}/users/me", json={"full_name": "Nome Novo"}, headers=auth_headers(user)
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Nome Novo"


async def test_update_me_email_conflict(
    client: AsyncClient, user: User, user_factory: UserFactory
) -> None:
    other = await user_factory()
    response = await client.patch(
        f"{API}/users/me", json={"email": other.email}, headers=auth_headers(user)
    )
    assert response.status_code == 409


async def test_admin_deactivates_user(client: AsyncClient, superuser: User, user: User) -> None:
    response = await client.patch(
        f"{API}/users/{user.id}", json={"is_active": False}, headers=auth_headers(superuser)
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert (await client.get(f"{API}/users/me", headers=auth_headers(user))).status_code == 401


async def test_admin_deletes_user(client: AsyncClient, superuser: User, user: User) -> None:
    headers = auth_headers(superuser)
    assert (await client.delete(f"{API}/users/{user.id}", headers=headers)).status_code == 204
    assert (await client.get(f"{API}/users/{user.id}", headers=headers)).status_code == 404


async def test_admin_cannot_delete_self(client: AsyncClient, superuser: User) -> None:
    response = await client.delete(f"{API}/users/{superuser.id}", headers=auth_headers(superuser))
    assert response.status_code == 400
