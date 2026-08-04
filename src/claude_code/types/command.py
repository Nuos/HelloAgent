"""用户请求类型，对应源码 users/request 与 commands 输入规范。

输入：CLI 原始文本。输出：规范化 UserRequest（任务文本 + 可选 slash 命令）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class UserRequest:
    """一条规范化后的用户请求。

    command：slash 命令名（如 read/edit/bash），None 表示普通文本任务；
    args：slash 命令参数；text：完整原始文本。
    """

    text: str
    command: str | None = None
    args: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, raw: str) -> UserRequest:
        """从原始输入解析出请求对象。

        输入：CLI 传入的原始字符串。输出：UserRequest（以 / 开头的解析为 slash 命令）。
        """
        stripped = raw.strip()
        if stripped.startswith("/") and len(stripped) > 1:
            parts = stripped[1:].split()
            return cls(text=stripped, command=parts[0], args=parts[1:])
        return cls(text=stripped)
