"""Agent 生命周期事件，对应源码 domain/events 与 QueryEngine 事件协议。

输入：引擎状态迁移。输出：不可变事件对象，供 CLI 渲染与测试断言。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from claude_code.types.ids import SessionId, ToolUseId, TurnId
from claude_code.types.messages import Message


@dataclass(frozen=True, slots=True)
class UserMessageAccepted:
    """用户请求被接收并进入会话。"""

    session_id: SessionId
    message: Message


@dataclass(frozen=True, slots=True)
class ModelTurnStarted:
    """模型调用开始。"""

    session_id: SessionId
    turn: TurnId


@dataclass(frozen=True, slots=True)
class AssistantTextDelta:
    """模型流式文本增量，直接转发给渲染层。"""

    session_id: SessionId
    turn: TurnId
    text: str


@dataclass(frozen=True, slots=True)
class ToolRequested:
    """工具调用请求已通过校验，待执行。"""

    session_id: SessionId
    turn: TurnId
    tool_use_id: ToolUseId
    name: str
    input: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolCompleted:
    """工具执行完成（成功或失败）。"""

    session_id: SessionId
    turn: TurnId
    tool_use_id: ToolUseId
    name: str
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class AgentCompleted:
    """Agent 正常结束（模型只返回文本或达到终止条件）。"""

    session_id: SessionId
    text: str


@dataclass(frozen=True, slots=True)
class AgentFailed:
    """Agent 异常终止（超过 max_turns、协议错误等）。"""

    session_id: SessionId
    reason: str


AgentEvent = (
    UserMessageAccepted
    | ModelTurnStarted
    | AssistantTextDelta
    | ToolRequested
    | ToolCompleted
    | AgentCompleted
    | AgentFailed
)
