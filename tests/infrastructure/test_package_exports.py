from __future__ import annotations

import pytest


@pytest.mark.unit
def test_package_init_exports():
    import coordinator
    import graph

    assert "run_session" in coordinator.__all__
    assert "run_session_async" in coordinator.__all__
    assert "run_assessment" in graph.__all__
    assert "run_assessment_async" in graph.__all__
