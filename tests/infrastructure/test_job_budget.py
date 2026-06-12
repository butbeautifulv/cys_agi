from __future__ import annotations

import pytest

from cys_core.security.job_budget import JobBudgetExceeded, JobBudgetTracker


@pytest.mark.unit
def test_job_budget_tool_call_limit():
    JobBudgetTracker.clear_all()
    JobBudgetTracker.configure("sess-1", max_tokens=1000, max_cost_usd=1.0, max_tool_calls=2)
    JobBudgetTracker.record_tool_call("sess-1")
    JobBudgetTracker.record_tool_call("sess-1")
    with pytest.raises(JobBudgetExceeded, match="tool-call"):
        JobBudgetTracker.record_tool_call("sess-1")
    JobBudgetTracker.clear_all()


@pytest.mark.unit
def test_job_budget_token_and_cost_limit(monkeypatch):
    JobBudgetTracker.clear_all()
    monkeypatch.setattr("cys_core.security.job_budget.settings.job_cost_per_1k_tokens_usd", 1.0)
    JobBudgetTracker.configure("sess-2", max_tokens=100, max_cost_usd=0.05, max_tool_calls=50)
    with pytest.raises(JobBudgetExceeded, match="token"):
        JobBudgetTracker.record_tokens("sess-2", 200)
    JobBudgetTracker.clear_all()
