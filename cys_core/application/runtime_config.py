from __future__ import annotations

from typing import Any

_stage: str = "dev"
_manual_investigation_async: bool = True
_use_conductor_for_events: bool = False
_max_spawn_depth: int = 5
_use_dynamic_catalog: bool = False
_use_memory_fallback: bool = False
_postgres_url: str = "postgresql://postgres:password@localhost:5432/cys_agi"
_default_job_recursion_limit: int = 25
_llm_model: str = "anthropic/claude-sonnet-4"
_llm_api_key: str = ""
_llm_base_url: str | None = None
_llm_temperature: float = 0.1
_llm_request_timeout: float = 120.0
_veil_mcp_url: str = "http://localhost:8091/mcp"
_veil_mcp_enabled: bool = True
_veil_mcp_timeout: float = 30.0
_veneno_mcp_url: str = "http://localhost:8093/mcp"
_veneno_mcp_enabled: bool = False
_veneno_mcp_timeout: float = 60.0
_planner_fallback_personas: str = "consultant"


def configure_from_settings(settings: Any) -> None:
    global _stage, _manual_investigation_async, _use_conductor_for_events
    global _max_spawn_depth, _use_dynamic_catalog, _use_memory_fallback
    global _postgres_url, _default_job_recursion_limit
    global _llm_model, _llm_api_key, _llm_base_url, _llm_temperature, _llm_request_timeout
    global _veil_mcp_url, _veil_mcp_enabled, _veil_mcp_timeout
    global _veneno_mcp_url, _veneno_mcp_enabled, _veneno_mcp_timeout, _planner_fallback_personas
    _stage = settings.stage
    _manual_investigation_async = settings.manual_investigation_async
    _use_conductor_for_events = settings.use_conductor_for_events
    _max_spawn_depth = settings.max_spawn_depth
    _use_dynamic_catalog = settings.use_dynamic_catalog
    _use_memory_fallback = settings.use_memory_fallback
    _postgres_url = settings.postgres_url
    _default_job_recursion_limit = settings.default_job_recursion_limit
    _llm_model = settings.llm_model
    _llm_api_key = settings.llm_api_key
    _llm_base_url = settings.llm_base_url
    _llm_temperature = settings.llm_temperature
    _llm_request_timeout = settings.llm_request_timeout
    _veil_mcp_url = settings.veil_mcp_url
    _veil_mcp_enabled = settings.veil_mcp_enabled
    _veil_mcp_timeout = settings.veil_mcp_timeout
    _veneno_mcp_url = settings.veneno_mcp_url
    _veneno_mcp_enabled = settings.veneno_mcp_enabled
    _veneno_mcp_timeout = settings.veneno_mcp_timeout
    _planner_fallback_personas = settings.planner_fallback_personas


def get_stage() -> str:
    return _stage


def get_manual_investigation_async() -> bool:
    return _manual_investigation_async


def get_use_conductor_for_events() -> bool:
    return _use_conductor_for_events


def get_max_spawn_depth() -> int:
    return _max_spawn_depth


def get_use_dynamic_catalog() -> bool:
    return _use_dynamic_catalog


def get_use_memory_fallback() -> bool:
    return _use_memory_fallback


def get_postgres_url() -> str:
    return _postgres_url


def get_default_job_recursion_limit() -> int:
    return _default_job_recursion_limit


def get_llm_settings() -> dict[str, object]:
    return {
        "model": _llm_model,
        "api_key": _llm_api_key,
        "base_url": _llm_base_url,
        "temperature": _llm_temperature,
        "request_timeout": _llm_request_timeout,
    }


def veil_mcp_enabled() -> bool:
    return _veil_mcp_enabled


def get_veil_mcp_url() -> str:
    return _veil_mcp_url


def get_veil_mcp_timeout() -> float:
    return _veil_mcp_timeout


def veneno_mcp_enabled() -> bool:
    return _veneno_mcp_enabled


def get_veneno_mcp_url() -> str:
    return _veneno_mcp_url


def get_veneno_mcp_timeout() -> float:
    return _veneno_mcp_timeout


def get_planner_fallback_personas() -> str:
    return _planner_fallback_personas
