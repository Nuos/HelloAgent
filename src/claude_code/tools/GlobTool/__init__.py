"""GlobTool：工作区内 glob 文件匹配，对应源码 tools/GlobTool/。

输入：pattern。输出：匹配文件相对路径列表（逗号分隔）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_code.Tool import Tool, ToolExecutionResult, ToolSpec
from claude_code.types.ids import ToolUseId


class GlobTool(Tool):
    """按 glob 模式列出工作区内文件。"""

    spec = ToolSpec(
        name="Glob",
        description="List files matching a glob pattern inside the workspace.",
        input_schema={
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "required": ["pattern"],
        },
        is_concurrency_safe=True,
    )

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, input: dict[str, Any], tool_use_id: ToolUseId) -> ToolExecutionResult:
        pattern = input.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            return ToolExecutionResult(tool_use_id, "Glob: missing string 'pattern'", is_error=True)
        root = self.workspace_root
        if pattern.startswith("/") or ".." in pattern.split("/"):
            return ToolExecutionResult(
                tool_use_id, "Glob: pattern must stay inside the workspace", is_error=True
            )
        try:
            matches = [str(p.relative_to(root)) for p in root.glob(pattern) if p.is_file()]
        except OSError as exc:
            return ToolExecutionResult(tool_use_id, f"Glob: {exc}", is_error=True)
        matches.sort()
        return ToolExecutionResult(tool_use_id, "\n".join(matches) if matches else "(no matches)")
