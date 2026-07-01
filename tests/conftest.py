from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _wire_bootstrap_container():
    """Ensure composition root registers loaders used by registry/catalog paths."""
    from bootstrap.container import get_container

    get_container()


@pytest.fixture(autouse=True)
def _disable_auth_by_default(monkeypatch):
    from bootstrap.settings import get_settings

    monkeypatch.setenv("AUTH_ENABLED", "0")
    monkeypatch.setenv("RBAC_ENABLED", "0")
    get_settings.cache_clear()
    from cys_core.infrastructure.auth import factory as auth_factory

    auth_factory.get_token_verifier.cache_clear()
