import pytest
from pydantic import ValidationError

from cys_core.domain.findings.models import CriticResult, FindingEnvelope, RedTeamFinding


@pytest.mark.unit
def test_red_team_finding_confidence_bounds():
    assert RedTeamFinding(confidence=0.5).confidence == 0.5
    with pytest.raises(ValidationError):
        RedTeamFinding(confidence=1.5)


@pytest.mark.unit
def test_critic_result_defaults():
    result = CriticResult()
    assert result.trust_score == 0.0
    assert result.issues_detected == []


@pytest.mark.unit
def test_finding_envelope_agent_literal():
    env = FindingEnvelope(agent="redteam", data={"severity": "low"})
    assert env.agent == "redteam"
    with pytest.raises(ValidationError):
        FindingEnvelope(agent="unknown", data={})
