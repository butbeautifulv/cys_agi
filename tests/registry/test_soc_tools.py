from __future__ import annotations

import pytest

from cys_core.registry.agents import get_agent_registry


@pytest.mark.unit
def test_soc_agent_includes_query_siem_readonly():
    soc = get_agent_registry().get("soc")
    assert "query_siem_readonly" in soc.tools
    assert "rag_query" in soc.tools
    assert "dedup_alerts" in soc.tools
