#!/usr/bin/env python3
"""Tests unitaires de securite pour hash mot de passe et JWT."""

from pathlib import Path
import sys
from datetime import timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password_roundtrip():
    plain = "SuperSecret42!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("bad-password", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token({"sub": "alice"}, expires_delta=timedelta(minutes=5))
    payload = decode_access_token(token)

    assert payload is not None
    assert payload.get("sub") == "alice"
    assert "exp" in payload


def test_decode_access_token_returns_none_for_invalid_token():
    assert decode_access_token("not-a-valid-token") is None
