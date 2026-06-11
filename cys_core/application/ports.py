from __future__ import annotations

from typing import Any, Protocol

from langchain_core.language_models.chat_models import BaseChatModel


class PersistenceContext(Protocol):
    """Storage-agnostic persistence context used by application services."""

    checkpointer: Any
    store: Any


class PersistenceConnector(Protocol):
    """Port for sync and async persistence connectors."""

    name: str

    def open(self, *, force_memory: bool | None = None) -> PersistenceContext:
        """Open a sync persistence context."""

    async def open_async(self, *, force_memory: bool | None = None) -> PersistenceContext:
        """Open an async persistence context."""


class ModelConnector(Protocol):
    """Port for swappable LLM/model backends."""

    name: str

    def create_model(self) -> BaseChatModel:
        """Create the configured chat model."""

    def callbacks(self) -> list[Any]:
        """Return optional tracing callbacks."""


class AgentTransportConnector(Protocol):
    """Port for inter-agent transport connectors."""

    name: str
    requires_mtls: bool

    def send(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send an A2A message over the connector."""

    async def send_async(self, message: dict[str, Any]) -> dict[str, Any]:
        """Send an A2A message over the connector asynchronously."""

    def subscribe(self, channel: str, handler: Any) -> None:
        """Register async handler for bus messages on channel."""

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        """Publish message to bus channel."""


class SandboxConnector(Protocol):
    """Port for ephemeral worker sandbox lifecycle."""

    name: str

    def create(self, run_id: str, persona: str, policy: str = "default") -> Any:
        """Provision isolated sandbox for one worker run."""

    def destroy(self, run_id: str) -> None:
        """Tear down sandbox after worker completes."""

    async def acreate(self, run_id: str, persona: str, policy: str = "default") -> Any:
        """Async provision sandbox."""

    async def adestroy(self, run_id: str) -> None:
        """Async tear down sandbox."""


class JobQueueConnector(Protocol):
    """Port for worker job queue."""

    name: str

    def enqueue(self, job: dict[str, Any]) -> str:
        """Enqueue worker job, return job id."""

    def dequeue(self, timeout: float = 0.0) -> dict[str, Any] | None:
        """Dequeue next job or None."""

    async def aenqueue(self, job: dict[str, Any]) -> str:
        """Async enqueue."""

    async def adequeue(self, timeout: float = 0.0) -> dict[str, Any] | None:
        """Async dequeue."""

