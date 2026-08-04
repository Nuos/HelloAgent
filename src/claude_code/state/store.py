"""会话状态存储，对应源码 state/store.ts 与 session 持久化概念。

输入：Message。输出：Session（append 追加、snapshot 返回不可变视图）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from claude_code.types.ids import SessionId
from claude_code.types.messages import Message


@dataclass(slots=True)
class Session:
    """一次会话的消息链与轮次计数。

    状态：messages 追加式列表、turn_count 已执行轮数。
    边界：本阶段仅内存态；JSONL 持久化属于后续阶段。
    """

    session_id: SessionId
    messages: list[Message] = field(default_factory=list)
    turn_count: int = 0

    def append(self, message: Message) -> None:
        """追加一条消息到会话尾部。"""
        self.messages.append(message)

    def snapshot(self) -> tuple[Message, ...]:
        """返回当前消息链的不可变快照。"""
        return tuple(self.messages)
