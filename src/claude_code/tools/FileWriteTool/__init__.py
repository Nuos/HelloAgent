"""FileWriteTool：工作区内文件写入，对应源码 tools/FileWriteTool/。

输入：path、content。输出：写入确认；越界/父目录缺失返回结构化错误。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_code.Tool import Tool, ToolExecutionResult, ToolSpec
from claude_code.types.ids import ToolUseId
from claude_code.utils.permissions import WorkspaceBoundaryError, resolve_path


class FileWriteTool(Tool):
    """写入或覆盖工作区内文本文件（不创建中间目录）。"""

    spec = ToolSpec(
        name="Write",
        description="Write text content to a workspace file (overwrites).",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        is_concurrency_safe=False,
    )

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, input: dict[str, Any], tool_use_id: ToolUseId) -> ToolExecutionResult:
        path_value = input.get("path")
        content_value = input.get("content")
        if not isinstance(path_value, str) or not isinstance(content_value, str):
            return ToolExecutionResult(
                tool_use_id, "Write: missing string path/content", is_error=True
            )
        try:
            path = resolve_path(self.workspace_root, path_value)
        except WorkspaceBoundaryError as exc:
            return ToolExecutionResult(tool_use_id, str(exc), is_error=True)
        if path.parent.exists() and not path.parent.is_dir():
            return ToolExecutionResult(
                tool_use_id, f"Write: parent is not a directory: {path.parent}", is_error=True
            )
        try:
            path.write_text(content_value, encoding="utf-8")
        except OSError as exc:
            return ToolExecutionResult(tool_use_id, f"Write: {exc}", is_error=True)
        return ToolExecutionResult(tool_use_id, f"Wrote {path} ({len(content_value)} chars)")
