"""停止钩子，对应源码 query/stopHooks.ts。

输入：模型轮次结果与轮次计数。输出：是否停止的判断。
"""

from __future__ import annotations

from typing import Protocol

from claude_code.types.messages import ModelTurn


class StopHook(Protocol):
    """停止条件判定边界。"""

    def should_stop(self, turn: ModelTurn, turns_used: int, max_turns: int) -> bool: ...


class MaxTurnsStopHook:
    """达到最大轮次时停止，防止工具循环无限执行。"""

    def should_stop(self, turn: ModelTurn, turns_used: int, max_turns: int) -> bool:
        return turns_used >= max_turns
