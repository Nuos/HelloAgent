"""工具契约，对应源码 Tool.ts。

输入：工具调用输入 dict。输出：ToolSpec 元数据 + ToolExecutionResult 结构化结果。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from claude_code.types.ids import ToolUseId
from claude_code.types.permissions import PermissionMode


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """工具声明：名称、描述、输入 Schema、并发与启用属性。"""

    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    is_concurrency_safe: bool = False
    is_enabled_by_default: bool = True


@dataclass(frozen=True, slots=True)
class ToolExecutionResult:
    """一次工具执行的返回值（成功或结构化失败）。"""

    tool_use_id: ToolUseId
    content: str
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class ToolPermissionContext:
    """工具执行时的权限上下文：模式与规则集合。"""

    mode: PermissionMode = PermissionMode.DEFAULT
    extra_directories: tuple[str, ...] = ()
    can_bypass: bool = False


class Tool(ABC):
    """工具基类：子类必须声明 spec 并实现 execute。

    边界：execute 内禁止绕过外部输入校验；失败以 ToolExecutionResult(is_error=True)
    返回，不向调用方抛业务异常。
    """

    spec: ToolSpec

    @abstractmethod
    def execute(self, input: dict[str, Any], tool_use_id: ToolUseId) -> ToolExecutionResult:
        """执行一次工具调用。

        输入：input 参数字典与工具调用 ID。输出：ToolExecutionResult。
        """
