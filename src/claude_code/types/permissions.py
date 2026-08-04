"""权限类型，对应源码 types/permissions.ts 与 utils/permissions/。

输入：权限规则与当前模式。输出：PermissionMode 与 PermissionDecision 决策类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PermissionMode(StrEnum):
    """权限模式，对应源码 permissions.ts 的模式谱系。

    plan：先形成计划再执行；default：常规交互；acceptEdits：工作区内自动批准；
    auto：ML 分类器辅助；dontAsk：不询问、未命中即拒绝；
    bypassPermissions：跳过大部分提示（保留关键检查）。
    """

    PLAN = "plan"
    DEFAULT = "default"
    ACCEPT_EDITS = "acceptEdits"
    AUTO = "auto"
    DONT_ASK = "dontAsk"
    BYPASS_PERMISSIONS = "bypassPermissions"


@dataclass(frozen=True, slots=True)
class PermissionDecision:
    """工具调用的授权决策，对应源码 PermissionDecision。"""

    behavior: str  # allow | ask | deny
    reason: str = ""
    updated_input: dict[str, Any] | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """一条权限规则：工具名模式 + 决策行为。"""

    tool_pattern: str
    behavior: str  # allow | ask | deny
    mode: PermissionMode | None = None
    extra: dict[str, Any] = field(default_factory=dict)
