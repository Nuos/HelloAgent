"""FileEditTool：工作区内唯一匹配替换，对应源码 tools/FileEditTool/。

输入：path、old_string、new_string。输出：替换后的文件文本；旧文本必须恰好出现一次。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_code.Tool import Tool, ToolExecutionResult, ToolSpec
from claude_code.types.ids import ToolUseId
from claude_code.utils.permissions import WorkspaceBoundaryError, resolve_path


class FileEditTool(Tool):
    """用 new_string 替换文件中恰好出现一次的 old_string。"""

    spec = ToolSpec(
        name="Edit",
        description="Replace a unique old_string with new_string in a workspace file.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
            },
            "required": ["path", "old_string", "new_string"],
        },
        is_concurrency_safe=False,
    )

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, input: dict[str, Any], tool_use_id: ToolUseId) -> ToolExecutionResult:
        path_value = input.get("path")
        old_value = input.get("old_string")
        new_value = input.get("new_string")
        if (
            not isinstance(path_value, str)
            or not isinstance(old_value, str)
            or not isinstance(new_value, str)
        ):
            return ToolExecutionResult(
                tool_use_id, "Edit: missing string path/old_string/new_string", is_error=True
            )
        try:
            path = resolve_path(self.workspace_root, path_value)
        except WorkspaceBoundaryError as exc:
            return ToolExecutionResult(tool_use_id, str(exc), is_error=True)
        if not path.is_file():
            return ToolExecutionResult(tool_use_id, f"Edit: not a file: {path}", is_error=True)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return ToolExecutionResult(tool_use_id, f"Edit: {exc}", is_error=True)
        count = content.count(old_value)
        if count != 1:
            return ToolExecutionResult(
                tool_use_id,
                f"Edit: old_string must match exactly once, found {count}",
                is_error=True,
            )
        new_content = content.replace(old_value, new_value)
        try:
            path.write_text(new_content, encoding="utf-8")
        except OSError as exc:
            return ToolExecutionResult(tool_use_id, f"Edit: {exc}", is_error=True)
        return ToolExecutionResult(tool_use_id, f"Edited {path}: {old_value!r} -> {new_value!r}")
