from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, TypeVar

from langchain.agents import create_agent
from langchain.agents.middleware.human_in_the_loop import HumanInTheLoopMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import tool
from pydantic import BaseModel

from config import settings
from cys_core.application.ports import ModelConnector
from cys_core.domain.agents.policies import build_interrupt_on
from cys_core.domain.messaging import extract_message_content
from cys_core.domain.security.exceptions import SecurityViolation
from cys_core.domain.security.factory import get_input_sanitizer, get_output_guardrails
from cys_core.domain.security.prompt_context import REFUSAL_MESSAGE
from cys_core.llm import get_model_connector
from cys_core.middleware.prompt_context_middleware import PromptContextMiddleware
from cys_core.middleware.scope_middleware import ScopeMiddleware
from cys_core.middleware.security_middleware import SecurityMiddleware
from cys_core.persistence import get_persistence_connector
from cys_core.registry.agents import AgentDefinition, AgentRegistry, get_agent_registry
from cys_core.registry.schemas import schema_registry
from cys_core.registry.tools import tool_registry

T = TypeVar("T", bound=BaseModel)


class AgentRuntime:
    """Single entry point for creating and running config-driven agents."""

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        model_connector: ModelConnector | None = None,
    ) -> None:
        self.registry = registry or get_agent_registry()
        self.model_connector = model_connector or get_model_connector()
        self.sanitizer = get_input_sanitizer()
        self.guardrails = get_output_guardrails()

    def _build_middleware(self, defn: AgentDefinition, session_id: str) -> list[Any]:
        middleware: list[Any] = [
            PromptContextMiddleware(
                agent_id=defn.name,
                system_prompt_digest=defn.system_prompt_digest,
                session_id=session_id,
                sanitizer=self.sanitizer,
                guardrails=self.guardrails,
            ),
            ScopeMiddleware(allowed_tools=defn.allowed_tools),
            SecurityMiddleware(agent_id=defn.name, session_id=session_id),
        ]
        interrupt_on = build_interrupt_on(defn.hitl_tools)
        if interrupt_on:
            middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_on))
        return middleware

    def create(
        self,
        defn: AgentDefinition,
        *,
        model: BaseChatModel | None = None,
        session_id: str = "default",
        use_checkpointer: bool = True,
        extra_tools: list | None = None,
    ):
        tools = tool_registry.resolve(defn.tools)
        if extra_tools:
            tools = [*tools, *extra_tools]

        checkpointer = None
        if use_checkpointer:
            checkpointer = get_persistence_connector().open(force_memory=True).checkpointer

        schema = schema_registry.get(defn.schema_name)
        return create_agent(
            model=model or self.model_connector.create_model(),
            tools=tools,
            system_prompt=defn.system_prompt,
            middleware=self._build_middleware(defn, session_id),
            response_format=schema,
            checkpointer=checkpointer,
            name=defn.name,
        )

    async def acreate(
        self,
        defn: AgentDefinition,
        *,
        model: BaseChatModel | None = None,
        session_id: str = "default",
        use_checkpointer: bool = True,
        extra_tools: list | None = None,
    ):
        tools = tool_registry.resolve(defn.tools)
        if extra_tools:
            tools = [*tools, *extra_tools]

        checkpointer = None
        if use_checkpointer:
            checkpointer = (await get_persistence_connector().open_async(force_memory=True)).checkpointer

        schema = schema_registry.get(defn.schema_name)
        return create_agent(
            model=model or self.model_connector.create_model(),
            tools=tools,
            system_prompt=defn.system_prompt,
            middleware=self._build_middleware(defn, session_id),
            response_format=schema,
            checkpointer=checkpointer,
            name=defn.name,
        )

    def run(
        self,
        name: str,
        user_input: str,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        defn = self.registry.get(name)
        sid = session_id or f"agent-{name}"
        agent = self.create(defn, session_id=sid)
        schema = schema_registry.get(defn.schema_name)
        return self._invoke(agent, user_input, session_id=sid, schema=schema)

    async def arun(
        self,
        name: str,
        user_input: str,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        defn = self.registry.get(name)
        sid = session_id or f"agent-{name}"
        agent = await self.acreate(defn, session_id=sid)
        schema = schema_registry.get(defn.schema_name)
        return await self._ainvoke(agent, user_input, session_id=sid, schema=schema)

    def _invoke(
        self,
        agent,
        user_input: str,
        *,
        session_id: str,
        schema: type[BaseModel] | None,
    ) -> dict[str, Any]:
        try:
            sanitized = self.sanitizer.sanitize(user_input, source="user")
        except SecurityViolation:
            return {"error": REFUSAL_MESSAGE}
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": self.model_connector.callbacks(),
            "recursion_limit": 25,
        }
        result = agent.invoke(
            {"messages": [{"role": "user", "content": sanitized}]},
            config=config,
        )
        return self._coerce_result(result, schema=schema)

    async def _ainvoke(
        self,
        agent,
        user_input: str,
        *,
        session_id: str,
        schema: type[BaseModel] | None,
    ) -> dict[str, Any]:
        try:
            sanitized = self.sanitizer.sanitize(user_input, source="user")
        except SecurityViolation:
            return {"error": REFUSAL_MESSAGE}
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": self.model_connector.callbacks(),
            "recursion_limit": 25,
        }
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": sanitized}]},
            config=config,
        )
        return self._coerce_result(result, schema=schema)

    def _coerce_result(
        self,
        result: dict[str, Any],
        *,
        schema: type[BaseModel] | None,
    ) -> dict[str, Any]:
        structured = result.get("structured_response")
        if structured is not None:
            data = structured.model_dump() if isinstance(structured, BaseModel) else dict(structured)
            if schema:
                validated = self.guardrails.validate_schema(data, schema)
                return validated.model_dump()
            return data

        messages = result.get("messages", [])
        if not messages:
            return {"error": "no response"}
        text = extract_message_content(messages[-1].content)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {"raw_response": text}

        if schema:
            try:
                validated = self.guardrails.validate_schema(data, schema)
                return validated.model_dump()
            except SecurityViolation:
                if settings.stage == "dev":
                    return data
                raise
        return self.guardrails.validate_output({"response": json.dumps(data, ensure_ascii=False)})

    def to_deep_agent_subagent(self, defn: AgentDefinition) -> dict[str, Any]:
        return {
            "name": defn.name,
            "description": defn.description,
            "system_prompt": defn.system_prompt,
            "tools": tool_registry.resolve(defn.tools),
        }


@lru_cache
def get_runtime() -> AgentRuntime:
    return AgentRuntime()


def make_assessment_pipeline_tool(runtime: AgentRuntime | None = None):
    """Factory for coordinator tool that runs LangGraph assessment."""
    from graph.workflow import run_assessment

    @tool
    def run_assessment_pipeline(input_text: str, thread_id: str = "deep-session") -> str:
        """Run the full LangGraph security assessment pipeline on authorized input."""
        result = run_assessment(
            input_text,
            thread_id=thread_id,
            persistence=get_persistence_connector().open(force_memory=True),
        )
        return json.dumps(result.get("report") or result, ensure_ascii=False, indent=2)

    return run_assessment_pipeline


def make_async_assessment_pipeline_tool(runtime: AgentRuntime | None = None):
    """Factory for coordinator async tool that runs LangGraph assessment."""
    from graph.workflow import run_assessment_async

    @tool
    async def run_assessment_pipeline(input_text: str, thread_id: str = "deep-session") -> str:
        """Run the full LangGraph security assessment pipeline on authorized input."""
        result = await run_assessment_async(
            input_text,
            thread_id=thread_id,
            persistence=await get_persistence_connector().open_async(force_memory=True),
        )
        return json.dumps(result.get("report") or result, ensure_ascii=False, indent=2)

    return run_assessment_pipeline
