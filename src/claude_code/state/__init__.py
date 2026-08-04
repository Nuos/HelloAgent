"""会话状态：Session 存储与消息投影，对应源码 state/ 目录。

输入：Message / Session。输出：追加后的会话与不可变消息视图。
"""

from claude_code.state.selectors import visible_messages
from claude_code.state.store import Session

__all__ = ["Session", "visible_messages"]
