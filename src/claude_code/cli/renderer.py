"""事件渲染，对应源码 cli/print.ts 与 structuredIO.ts 的渲染边界。

输入：AgentEvent。输出：终端可读文本行。
"""

from __future__ import annotations

from claude_code.types.events import (
    AgentCompleted,
    AgentEvent,
    AgentFailed,
    AssistantTextDelta,
    ModelTurnStarted,
    ToolCompleted,
    ToolRequested,
    UserMessageAccepted,
)


def render_event(event: AgentEvent) -> str | None:
    """把事件渲染为一行文本；无需渲染的事件返回 None。"""
    if isinstance(event, AssistantTextDelta):
        return event.text
    if isinstance(event, UserMessageAccepted):
        return None
    if isinstance(event, ModelTurnStarted):
        return None
    if isinstance(event, ToolRequested):
        return f"\n⚙ {event.name}({_compact(event.input)})"
    if isinstance(event, ToolCompleted):
        return f"  ↳ {'failed' if event.is_error else 'done'}"
    if isinstance(event, AgentCompleted):
        return f"\n{event.text}"
    if isinstance(event, AgentFailed):
        return f"\n✗ Agent failed: {event.reason}"
    return None


def _compact(input: dict[str, object]) -> str:
    """把工具输入压成单行摘要。"""
    parts = [f"{key}={value}" for key, value in input.items() if value is not None]
    return ", ".join(parts) if parts else ""
