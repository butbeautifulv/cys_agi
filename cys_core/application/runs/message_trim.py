from __future__ import annotations

from langchain_core.messages import AIMessage, AnyMessage, ToolMessage


def trim_tool_results(messages: list[AnyMessage], *, keep: int = 3) -> list[AnyMessage]:
    """Keep only the last N tool result messages (DeepAgent keep_tool_result pattern)."""
    if keep <= 0:
        return messages
    tool_indices = [i for i, msg in enumerate(messages) if isinstance(msg, ToolMessage)]
    if len(tool_indices) <= keep:
        return messages
    drop = set(tool_indices[:-keep])
    trimmed = [msg for i, msg in enumerate(messages) if i not in drop]
    return heal_orphaned_tool_messages(trimmed)


def heal_orphaned_tool_messages(messages: list[AnyMessage]) -> list[AnyMessage]:
    """Drop leading tool results without a preceding assistant tool_call (DeepAgent pattern)."""
    trimmed = list(messages)
    while trimmed:
        first = trimmed[0]
        if isinstance(first, ToolMessage):
            trimmed.pop(0)
            continue
        role = getattr(first, "type", "") or getattr(first, "role", "")
        content = getattr(first, "content", "")
        if role == "tool":
            trimmed.pop(0)
            continue
        if role == "user" and isinstance(content, list):
            if any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content):
                trimmed.pop(0)
                continue
        break
    return trimmed
