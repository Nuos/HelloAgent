"""GrepTool：工作区内正则内容搜索，对应源码 tools/GrepTool/。

输入：pattern、path(可选)。输出：匹配行（相对路径:行号:内容）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from claude_code.Tool import Tool, ToolExecutionResult, ToolSpec
from claude_code.types.ids import ToolUseId
from claude_code.utils.permissions import WorkspaceBoundaryError, resolve_path

_MAX_MATCHES = 200


class GrepTool(Tool):
    """在文件或整个工作区内按正则搜索文本。"""

    spec = ToolSpec(
        name="Grep",
        description="Search file contents by regex inside the workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["pattern"],
        },
        is_concurrency_safe=True,
    )

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, input: dict[str, Any], tool_use_id: ToolUseId) -> ToolExecutionResult:
        pattern = input.get("pattern")
        path_value = input.get("path")
        if not isinstance(pattern, str) or not pattern:
            return ToolExecutionResult(tool_use_id, "Grep: missing string 'pattern'", is_error=True)
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return ToolExecutionResult(tool_use_id, f"Grep: bad pattern: {exc}", is_error=True)
        root = self.workspace_root
        target_dir = root
        if path_value is not None:
            if not isinstance(path_value, str) or not path_value:
                return ToolExecutionResult(tool_use_id, "Grep: invalid 'path'", is_error=True)
            try:
                target_dir = resolve_path(root, path_value)
            except WorkspaceBoundaryError as exc:
                return ToolExecutionResult(tool_use_id, str(exc), is_error=True)
            if not target_dir.is_dir():
                return ToolExecutionResult(
                    tool_use_id, f"Grep: not a directory: {target_dir}", is_error=True
                )
        results: list[str] = []
        try:
            for path in target_dir.rglob("*"):
                if not path.is_file():
                    continue
                try:
                    rel = str(path.relative_to(root))
                    for lineno, line in enumerate(
                        path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                    ):
                        if regex.search(line):
                            results.append(f"{rel}:{lineno}:{line}")
                            if len(results) >= _MAX_MATCHES:
                                results.append("...[truncated]")
                                break
                except OSError:
                    continue
                if len(results) >= _MAX_MATCHES + 1:
                    break
        except OSError as exc:
            return ToolExecutionResult(tool_use_id, f"Grep: {exc}", is_error=True)
        return ToolExecutionResult(tool_use_id, "\n".join(results) if results else "(no matches)")
