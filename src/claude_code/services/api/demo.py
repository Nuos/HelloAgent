"""DemoModelClient：确定性离线模型替身。

对应源码 services/api/claude.js 的模型边界；用于无网络/无 API Key 调试 Agent Loop。
解析最后一条 user 消息的 slash 语法（/read、/edit、/write、/bash、/glob、/grep）
为结构化 ToolCall，其余输入返回固定文本响应。
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

from claude_code.Tool import ToolSpec
from claude_code.types.ids import ToolUseId
from claude_code.types.messages import (
    Message,
    ModelStreamEvent,
    ModelTextDelta,
    ModelTurnCompleted,
    Role,
    ToolCall,
)

TOOL_ARG_MAP: dict[str, list[str]] = {
    "read": ["path"],
    "edit": ["path", "old_string", "new_string"],
    "write": ["path", "content"],
    "bash": ["command"],
    "glob": ["pattern"],
    "grep": ["pattern", "path"],
}


def _parse_slash(raw: str) -> tuple[str, dict[str, Any]] | None:
    """解析 slash 语法为 (工具名, 参数)。非法语法返回 None 交给文本路径。"""
    stripped = raw.strip()
    if not stripped.startswith("/") or len(stripped) <= 1:
        return None
    parts = stripped[1:].split()
    tool = parts[0].lower()
    arg_names = TOOL_ARG_MAP.get(tool)
    if arg_names is None:
        return None
    args = parts[1:]
    if tool == "edit":
        if len(args) < 3:
            return None
        return "Edit", {"path": args[0], "old_string": args[1], "new_string": " ".join(args[2:])}
    if tool == "bash":
        if not args:
            return None
        return "Bash", {"command": " ".join(args)}
    if tool == "write":
        if len(args) < 2:
            return None
        return "Write", {"path": args[0], "content": " ".join(args[1:])}
    if tool == "grep":
        return "Grep", {"pattern": args[0], "path": args[1] if len(args) > 1 else None}
    if not args:
        return None
    return tool.capitalize(), {arg_names[0]: " ".join(args)}


class DemoModelClient:
    """实现 ModelClient 协议的演示模型。"""

    name = "demo"

    async def stream(
        self,
        messages: Sequence[Message],
        tool_specs: Sequence[ToolSpec],
    ) -> AsyncIterator[ModelStreamEvent]:
        """按最后一条 user 消息产出事件流（文本增量或工具调用）。

        边界：工具结果回灌后（最后一条为 tool 消息）不再重复解析 slash，
        返回文本汇总，保证工具路径能正常终止。
        """
        spec_names = {spec.name for spec in tool_specs}
        if messages and messages[-1].is_tool_result:
            results = [
                m.tool_result.content if m.tool_result else "" for m in messages if m.is_tool_result
            ]
            latest = results[-1] if results else ""
            text = f"[demo] executed {len(results)} tool call(s). Latest result: {latest[:200]}"
            yield ModelTurnCompleted(text=text)
            return
        user_text = ""
        for message in reversed(messages):
            if message.role is Role.USER:
                user_text = message.content
                break
        parsed = _parse_slash(user_text)
        if parsed is not None:
            tool_name, tool_input = parsed
            if tool_name not in spec_names:
                yield ModelTurnCompleted(
                    text=f"tool '{tool_name}' is not available in this session",
                )
                return
            tool_use_id = ToolUseId(f"demo-{tool_name.lower()}-1")
            yield ModelTurnCompleted(
                text="",
                tool_calls=(ToolCall(id=tool_use_id, name=tool_name, input=tool_input),),
            )
            return
        text = f"[demo] received: {user_text.strip() or '(empty)'}"
        mid = max(1, len(text) // 2)
        yield ModelTextDelta(text=text[:mid])
        yield ModelTextDelta(text=text[mid:])
        yield ModelTurnCompleted(text=text)
