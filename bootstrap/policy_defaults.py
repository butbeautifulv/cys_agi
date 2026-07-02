from __future__ import annotations

from cys_core.domain.policy.defaults import DEFAULT_PROFILE_ID, default_profile_policy_payload


def default_profile_policy():
    return default_profile_policy_payload()


def default_profile_pack(*, id: str, default_personas: list[str]):
    from cys_core.domain.catalog.models import ProfilePack
    from cys_core.registry.product_context import get_product_context

    product = get_product_context()
    return ProfilePack(
        id=id,
        name="Cybersec SOC" if id == DEFAULT_PROFILE_ID else id,
        description="Filesystem seed profile",
        default_personas=default_personas,
        default_plan=product.manifest.default_plan,
        global_rules=product.rules_block,
        policy=default_profile_policy(),
    )
