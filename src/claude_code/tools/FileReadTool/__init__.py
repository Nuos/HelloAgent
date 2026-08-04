"""FileReadTool：工作区内文件读取，对应源码 tools/FileReadTool/。

输入：path。输出：文件文本；越界/不存在返回结构化错误。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_code.Tool import Tool, ToolExecutionResult, ToolSpec
from claude_code.types.ids import ToolUseId
from claude_code.utils.permissions import WorkspaceBoundaryError, resolve_path


class FileReadTool(Tool):
    """读取工作区内文本文件。"""

    spec = ToolSpec(
        name="Read",
        description="Read a text file inside the workspace.",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        is_concurrency_safe=True,
    )

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, input: dict[str, Any], tool_use_id: ToolUseId) -> ToolExecutionResult:
        path_value = input.get("path")
        if not isinstance(path_value, str) or not path_value:
            return ToolExecutionResult(tool_use_id, "Read: missing string 'path'", is_error=True)
        try:
            path = resolve_path(self.workspace_root, path_value)
        except WorkspaceBoundaryError as exc:
            return ToolExecutionResult(tool_use_id, str(exc), is_error=True)
        if not path.is_file():
            return ToolExecutionResult(tool_use_id, f"Read: not a file: {path}", is_error=True)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return ToolExecutionResult(tool_use_id, f"Read: {exc}", is_error=True)
        return ToolExecutionResult(tool_use_id, content)
