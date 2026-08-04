"""工具池：装配与执行入口，对应源码 tools.ts（assembleToolPool）与 Tool.ts。

输入：工作区根目录与 Bash 启用开关。输出：ToolRegistry（注册、查找、执行、结构化错误）。
"""

from __future__ import annotations

from pathlib import Path

from claude_code.Tool import Tool, ToolSpec
from claude_code.tools.BashTool import BashTool
from claude_code.tools.FileEditTool import FileEditTool
from claude_code.tools.FileReadTool import FileReadTool
from claude_code.tools.FileWriteTool import FileWriteTool
from claude_code.tools.GlobTool import GlobTool
from claude_code.tools.GrepTool import GrepTool
from claude_code.tools.registry import ToolRegistry
from claude_code.types.ids import ToolUseId


def assemble_tool_pool(workspace_root: Path, enable_bash: bool = False) -> ToolRegistry:
    """装配内置工具池。

    输入：workspace_root 工作区根、enable_bash 是否注册 Bash 工具。
    输出：ToolRegistry；Bash 默认不注册（deny-first 语义）。
    """
    tools: list[Tool] = [
        FileReadTool(workspace_root),
        FileEditTool(workspace_root),
        FileWriteTool(workspace_root),
        GlobTool(workspace_root),
        GrepTool(workspace_root),
    ]
    if enable_bash:
        tools.append(BashTool(workspace_root))
    return ToolRegistry(tools)


__all__ = ["Tool", "ToolRegistry", "ToolSpec", "ToolUseId", "assemble_tool_pool"]
