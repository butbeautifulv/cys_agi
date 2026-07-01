from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class WorkTodo(BaseModel):
    id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING
    assigned_persona: str = ""
    depends_on: list[str] = Field(default_factory=list)


class ClarifyingQuestion(BaseModel):
    id: str
    question: str
    required: bool = True


class WorkPlan(BaseModel):
    questions: list[ClarifyingQuestion] = Field(default_factory=list)
    todos: list[WorkTodo] = Field(default_factory=list)
    proposed_workers: list[str] = Field(default_factory=list)
    rationale: str = ""
    awaiting_user_input: bool = False


class PlanApproval(BaseModel):
    decision: Literal["approve", "reject", "edit"]
    edited_plan: WorkPlan | None = None
    actor: str = "operator"
