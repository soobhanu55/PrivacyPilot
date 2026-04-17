from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    hashed = hash_password("demo1234")
    assert verify_password("demo1234", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip() -> None:
    token = create_access_token("demo-sme")
    assert decode_access_token(token) == "demo-sme"


def test_refresh_token_roundtrip() -> None:
    token = create_refresh_token("demo-sme")
    assert decode_refresh_token(token) == "demo-sme"
