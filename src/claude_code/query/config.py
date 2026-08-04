"""查询配置，对应源码 query/config.ts（QueryConfig）。

输入：会话 ID 与运行参数。输出：不可变 QueryConfig（maxTurns、模型名、系统提示）。
"""

from __future__ import annotations

from dataclasses import dataclass

from claude_code.types.ids import SessionId


@dataclass(frozen=True, slots=True)
class QueryConfig:
    """一次查询的不可变配置，进入查询入口后不再变化。"""

    session_id: SessionId
    max_turns: int = 10
    model_name: str = "demo"
    system_prompt: str = "You are Claude Code, an AI coding agent."
