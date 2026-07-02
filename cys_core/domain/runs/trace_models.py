from __future__ import annotations

from pydantic import BaseModel, Field


class TraceVerdict(BaseModel):
    """Result of action-trace doubter-lite evaluation."""

    score: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict: str = ""
    reasoning: str = ""
    should_rerun: bool = False
    issues: list[str] = Field(default_factory=list)
