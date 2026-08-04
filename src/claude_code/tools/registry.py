"""工具注册表：注册、查找、执行、错误归一，对应源码 tools.ts 工具池逻辑。

输入：工具列表 + 调用 (name, input, tool_use_id)。输出：ToolExecutionResult。
"""

from __future__ import annotations

from typing import Any

from claude_code.Tool import Tool, ToolExecutionResult, ToolSpec
from claude_code.types.ids import ToolUseId


class ToolRegistry:
    """按名称管理工具并统一执行入口。

    边界：未知工具与工具内部异常都转成结构化 ToolExecutionResult，
    不向调用方抛业务异常。
    """

    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: Tool) -> None:
        """注册工具；重名工具覆盖（内置工具优先语义）。"""
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> Tool | None:
        """按名称取工具，未注册返回 None。"""
        return self._tools.get(name)

    def specs(self) -> tuple[ToolSpec, ...]:
        """返回全部已注册工具的规格。"""
        return tuple(tool.spec for tool in self._tools.values())

    def names(self) -> tuple[str, ...]:
        """返回全部已注册工具名。"""
        return tuple(self._tools.keys())

    def execute(
        self, name: str, input: dict[str, Any], tool_use_id: ToolUseId
    ) -> ToolExecutionResult:
        """执行一次工具调用。

        输入：工具名、参数字典、工具调用 ID。输出：ToolExecutionResult；
        未知工具与执行异常均以 is_error=True 返回。
        """
        tool = self._tools.get(name)
        if tool is None:
            return ToolExecutionResult(tool_use_id, f"unknown tool: {name}", is_error=True)
        try:
            return tool.execute(input, tool_use_id)
        except Exception as exc:
            return ToolExecutionResult(tool_use_id, f"{name} failed: {exc}", is_error=True)
