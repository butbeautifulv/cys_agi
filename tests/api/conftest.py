from __future__ import annotations

import json
import base64

import pytest

from cys_core.domain.security.auth_models import AuthClaims, AuthError, claims_from_payload


def _decode_test_token(token: str) -> dict:
    pad = "=" * (-len(token) % 4)
    return json.loads(base64.urlsafe_b64decode(token + pad).decode())


@pytest.fixture
def auth_settings(monkeypatch):
    from bootstrap.settings import get_settings

    monkeypatch.setenv("AUTH_ENABLED", "1")
    monkeypatch.setenv("RBAC_ENABLED", "1")
    monkeypatch.setenv("KEYCLOAK_ISSUER", "https://auth.test/realms/egregore")
    monkeypatch.setenv("KEYCLOAK_CLIENT_ID", "egregore-api")
    monkeypatch.setenv("KEYCLOAK_AUDIENCE", "egregore-api")
    get_settings.cache_clear()
    from cys_core.infrastructure.auth import factory as auth_factory

    auth_factory.get_token_verifier.cache_clear()

    roles = {
        "ingress": "egregore-ingress",
        "operator": "egregore-operator",
        "reader": "egregore-reader",
    }

    class _FakeVerifier:
        def verify_bearer(self, authorization_header: str | None) -> AuthClaims:
            if not authorization_header or not authorization_header.lower().startswith("bearer "):
                raise AuthError("missing bearer token")
            token = authorization_header.split(None, 1)[1]
            payload = _decode_test_token(token)
            return claims_from_payload(payload, client_id="egregore-api")

    verifier = _FakeVerifier()
    monkeypatch.setattr(auth_factory, "get_token_verifier", lambda: verifier)
    monkeypatch.setattr("interfaces.api.auth.get_token_verifier", lambda: verifier)

    def _token(role_names: list[str]) -> str:
        payload = {
            "sub": "test-user",
            "realm_access": {"roles": role_names},
            "resource_access": {"egregore-api": {"roles": role_names}},
        }
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    return {"roles": roles, "token": _token}
