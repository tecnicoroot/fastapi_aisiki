import jwt
import pytest

from fastapi_aisiki.core.security import (
    create_token,
    decode_token,
    generate_reset_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    hashed = hash_password("minha-senha")
    assert hashed != "minha-senha"
    assert verify_password("minha-senha", hashed)
    assert not verify_password("outra", hashed)


def test_token_roundtrip() -> None:
    token = create_token("abc", "access", token_version=3)
    payload = decode_token(token)
    assert payload["sub"] == "abc"
    assert payload["type"] == "access"
    assert payload["ver"] == 3


def test_tampered_token_is_rejected() -> None:
    token = create_token("abc", "access", token_version=0)
    with pytest.raises(jwt.PyJWTError):
        decode_token(token[:-2] + "xx")


def test_reset_token_hash() -> None:
    raw, hashed = generate_reset_token()
    assert hash_token(raw) == hashed
    assert raw != hashed
