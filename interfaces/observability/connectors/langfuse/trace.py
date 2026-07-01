from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from bootstrap.settings import settings

logger = logging.getLogger(__name__)


@lru_cache
def _ensure_langfuse_client() -> bool:
    if not settings.langfuse_enabled:
        return False
    try:
        from langfuse import Langfuse

        Langfuse(
            public_key=settings.resolved_langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.resolved_langfuse_host,
        )
        return True
    except Exception:
        logger.warning("Failed to initialize Langfuse client", exc_info=True)
        return False


class LangfuseTraceBackend:
    """Trace backend — single owner of Langfuse SDK lifecycle."""

    def get_callback_handler(self) -> Any | None:
        if not _ensure_langfuse_client():
            return None
        try:
            from langfuse.langchain import CallbackHandler

            return CallbackHandler()
        except Exception:
            logger.warning("Failed to create Langfuse CallbackHandler", exc_info=True)
            return None

    def start_span(self, ctx) -> str:
        return ctx.trace_id or ctx.span_name

    def end_span(self, span_id: str) -> None:
        _ = span_id

    def flush(self) -> None:
        if not settings.langfuse_enabled:
            return
        try:
            from langfuse import get_client

            get_client().flush()
        except Exception:
            logger.warning("Failed to flush Langfuse client", exc_info=True)

    def shutdown(self) -> None:
        if not settings.langfuse_enabled:
            return
        try:
            from langfuse import get_client

            client = get_client()
            client.flush()
            client.shutdown()
        except Exception:
            logger.warning("Failed to shutdown Langfuse client", exc_info=True)


class CompositeTraceBackend:
    """Fan-out trace events to multiple backends."""

    def __init__(self, *backends) -> None:
        self._backends = backends

    def get_callback_handler(self) -> Any | None:
        for backend in self._backends:
            handler = backend.get_callback_handler()
            if handler is not None:
                return handler
        return None

    def start_span(self, ctx) -> str:
        ids = [backend.start_span(ctx) for backend in self._backends]
        return ids[0] if ids else ""

    def end_span(self, span_id: str) -> None:
        for backend in self._backends:
            backend.end_span(span_id)

    def flush(self) -> None:
        for backend in self._backends:
            backend.flush()

    def shutdown(self) -> None:
        for backend in self._backends:
            backend.shutdown()
