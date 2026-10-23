from httpx import AsyncClient

from fastapi_aisiki.models import User
from tests.conftest import auth_headers

API = "/api/v1"


async def test_create_profile(client: AsyncClient, superuser: User) -> None:
    response = await client.post(
        f"{API}/profiles",
        json={"name": "suporte", "description": "Equipe de suporte"},
        headers=auth_headers(superuser),
    )
    assert response.status_code == 201
    assert response.json()["name"] == "suporte"


async def test_create_duplicate_profile(client: AsyncClient, superuser: User) -> None:
    response = await client.post(
        f"{API}/profiles", json={"name": "admin"}, headers=auth_headers(superuser)
    )
    assert response.status_code == 409


async def test_invalid_profile_name(client: AsyncClient, superuser: User) -> None:
    response = await client.post(
        f"{API}/profiles", json={"name": "Nome Inválido"}, headers=auth_headers(superuser)
    )
    assert response.status_code == 422


async def test_regular_user_cannot_create_profile(client: AsyncClient, user: User) -> None:
    response = await client.post(f"{API}/profiles", json={"name": "x1"}, headers=auth_headers(user))
    assert response.status_code == 403


async def test_regular_user_can_list_profiles(client: AsyncClient, user: User) -> None:
    response = await client.get(f"{API}/profiles", headers=auth_headers(user))
    assert response.status_code == 200
    assert {p["name"] for p in response.json()["items"]} == {"admin", "user"}


async def test_update_and_delete_profile(client: AsyncClient, superuser: User) -> None:
    headers = auth_headers(superuser)
    created = (await client.post(f"{API}/profiles", json={"name": "temp"}, headers=headers)).json()

    response = await client.patch(
        f"{API}/profiles/{created['id']}", json={"description": "Atualizado"}, headers=headers
    )
    assert response.json()["description"] == "Atualizado"

    assert (
        await client.delete(f"{API}/profiles/{created['id']}", headers=headers)
    ).status_code == 204
    assert (await client.get(f"{API}/profiles/{created['id']}", headers=headers)).status_code == 404
