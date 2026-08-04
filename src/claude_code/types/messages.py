"""消息与模型轮次类型，对应源码 query.ts 中的消息协议。

输入：角色、内容、工具调用。输出：不可变 Message / ModelTurn / ToolCall。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from claude_code.types.ids import ToolUseId


class Role(StrEnum):
    """消息角色，对应源码 Role 枚举。"""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class ToolCall:
    """结构化工具调用，对应源码 ToolCall。"""

    id: ToolUseId
    name: str
    input: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolResult:
    """工具执行结果，对应源码 tool_result 消息。"""

    tool_use_id: ToolUseId
    content: str
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class Message:
    """会话中的一条消息，对应源码 Message。"""

    role: Role
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_result: ToolResult | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_tool_use(self) -> bool:
        return self.role is Role.ASSISTANT and bool(self.tool_calls)

    @property
    def is_tool_result(self) -> bool:
        return self.role is Role.TOOL and self.tool_result is not None


@dataclass(frozen=True, slots=True)
class ModelTextDelta:
    """模型流式文本增量，对应源码 ModelTextDelta。"""

    text: str


@dataclass(frozen=True, slots=True)
class ModelTurnCompleted:
    """模型一轮输出完成，对应源码 ModelTurnCompleted。"""

    text: str
    tool_calls: tuple[ToolCall, ...] = ()


ModelStreamEvent = ModelTextDelta | ModelTurnCompleted
ModelTurnEnd = Literal["completed"]


@dataclass(frozen=True, slots=True)
class ModelTurn:
    """一次模型调用的完整结果（文本 + 可选工具调用）。"""

    text: str
    tool_calls: tuple[ToolCall, ...] = ()
