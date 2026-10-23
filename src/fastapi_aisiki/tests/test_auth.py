from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient

from app.core.queue import TaskName
from app.models import User
from tests.conftest import DEFAULT_PASSWORD, FakeQueue, auth_headers

API = "/api/v1"


async def _login(
    client: AsyncClient, email: str, password: str = DEFAULT_PASSWORD
) -> dict[str, str]:
    response = await client.post(
        f"{API}/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 200, response.text
    data: dict[str, str] = response.json()
    return data


async def test_register_assigns_default_profile_and_enqueues_email(
    client: AsyncClient, fake_queue: FakeQueue
) -> None:
    payload = {"email": "Novo@Example.com", "full_name": "Novo Usuário", "password": "Senha@123"}
    response = await client.post(f"{API}/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "novo@example.com"
    assert [p["name"] for p in body["profiles"]] == ["user"]
    assert "hashed_password" not in body
    assert fake_queue.jobs[0][0] == TaskName.SEND_WELCOME_EMAIL


async def test_register_duplicate_email(client: AsyncClient, user: User) -> None:
    payload = {"email": user.email, "full_name": "Outro", "password": "Senha@123"}
    response = await client.post(f"{API}/auth/register", json=payload)
    assert response.status_code == 409


async def test_register_weak_password(client: AsyncClient) -> None:
    payload = {"email": "a@example.com", "full_name": "Fulano", "password": "123"}
    response = await client.post(f"{API}/auth/register", json=payload)
    assert response.status_code == 422


async def test_login_and_me(client: AsyncClient, user: User) -> None:
    tokens = await _login(client, user.email)
    response = await client.get(
        f"{API}/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == user.email


async def test_login_wrong_password(client: AsyncClient, user: User) -> None:
    response = await client.post(
        f"{API}/auth/login", data={"username": user.email, "password": "errada123"}
    )
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/auth/login", data={"username": "nao@existe.com", "password": "qualquer1"}
    )
    assert response.status_code == 401


async def test_inactive_user_cannot_login(client: AsyncClient, user: User) -> None:
    user.is_active = False
    response = await client.post(
        f"{API}/auth/login", data={"username": user.email, "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 401


async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"{API}/users/me")
    assert response.status_code == 401


async def test_refresh_token(client: AsyncClient, user: User) -> None:
    tokens = await _login(client, user.email)
    response = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_access_token_cannot_be_used_as_refresh(client: AsyncClient, user: User) -> None:
    tokens = await _login(client, user.email)
    response = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert response.status_code == 401


async def test_password_recovery_flow(
    client: AsyncClient, user: User, fake_queue: FakeQueue
) -> None:
    old_headers = auth_headers(user)

    response = await client.post(f"{API}/auth/forgot-password", json={"email": user.email})
    assert response.status_code == 202

    task, kwargs = fake_queue.jobs[-1]
    assert task == TaskName.SEND_PASSWORD_RESET_EMAIL
    token = parse_qs(urlparse(kwargs["reset_url"]).query)["token"][0]

    response = await client.post(
        f"{API}/auth/reset-password", json={"token": token, "new_password": "NovaSenha@1"}
    )
    assert response.status_code == 200

    # Login com a nova senha funciona; tokens antigos foram revogados.
    await _login(client, user.email, "NovaSenha@1")
    assert (await client.get(f"{API}/users/me", headers=old_headers)).status_code == 401

    # Token de recuperação é de uso único.
    response = await client.post(
        f"{API}/auth/reset-password", json={"token": token, "new_password": "Outra@12345"}
    )
    assert response.status_code == 400


async def test_forgot_password_unknown_email_does_not_leak(
    client: AsyncClient, fake_queue: FakeQueue
) -> None:
    response = await client.post(f"{API}/auth/forgot-password", json={"email": "x@example.com"})
    assert response.status_code == 202
    assert fake_queue.jobs == []


async def test_reset_password_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/auth/reset-password", json={"token": "invalido", "new_password": "Senha@12345"}
    )
    assert response.status_code == 400


async def test_change_password(client: AsyncClient, user: User) -> None:
    response = await client.post(
        f"{API}/auth/change-password",
        json={"current_password": DEFAULT_PASSWORD, "new_password": "Trocada@123"},
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    await _login(client, user.email, "Trocada@123")
