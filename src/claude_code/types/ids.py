"""类型化 ID，对应源码 types/ids.ts。

输入：无。输出：SessionId/AgentId/TurnId/ToolUseId/MessageUuid 五个 NewType。
"""

from typing import NewType

SessionId = NewType("SessionId", str)
AgentId = NewType("AgentId", str)
TurnId = NewType("TurnId", str)
ToolUseId = NewType("ToolUseId", str)
MessageUuid = NewType("MessageUuid", str)
