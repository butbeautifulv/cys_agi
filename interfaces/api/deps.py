from __future__ import annotations

from cys_core.domain.security.auth_models import AuthClaims


def api_actor(auth: AuthClaims | None) -> str:
    """Resolve audit actor id from optional JWT claims."""
    return getattr(auth, "sub", "api") if auth else "api"
