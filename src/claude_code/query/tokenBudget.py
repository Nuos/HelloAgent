"""Token 预算，对应源码 query/tokenBudget.ts。

输入：文本。输出：估算字符数与预算检查结果。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenBudget:
    """按字符数粗略估算 token 占用的预算器（约 4 字符/token）。"""

    limit: int

    def estimate_chars(self, text: str) -> int:
        """估算文本字符数。"""
        return len(text)

    def would_exceed(self, text: str) -> bool:
        """文本是否超出预算上限。"""
        return self.estimate_chars(text) > self.limit
