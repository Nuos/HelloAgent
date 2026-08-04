"""会话消息投影，对应源码 state/selectors.ts。

输入：Session 与窗口大小 limit。输出：可见消息元组（默认全量）。
"""

from __future__ import annotations

from claude_code.state.store import Session
from claude_code.types.messages import Message


def visible_messages(session: Session, limit: int | None = None) -> tuple[Message, ...]:
    """取最近 limit 条消息；limit 为 None 时返回全部。"""
    msgs = session.messages
    if limit is None or limit >= len(msgs):
        return tuple(msgs)
    return tuple(msgs[-limit:])
