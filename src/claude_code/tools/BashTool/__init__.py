"""BashTool：工作区内命令执行（显式启用），对应源码 tools/BashTool/。

输入：command、timeout。输出：stdout/stderr 合并文本；受 cwd/timeout/输出截断约束。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from claude_code.Tool import Tool, ToolExecutionResult, ToolSpec
from claude_code.types.ids import ToolUseId

_DEFAULT_TIMEOUT = 30
_MAX_OUTPUT_CHARS = 8000


class BashTool(Tool):
    """在固定工作目录内执行 shell 命令，默认超时 30s、输出截断 8000 字符。"""

    spec = ToolSpec(
        name="Bash",
        description="Execute a shell command inside the workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "number"},
            },
            "required": ["command"],
        },
        is_concurrency_safe=False,
        is_enabled_by_default=False,
    )

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def execute(self, input: dict[str, Any], tool_use_id: ToolUseId) -> ToolExecutionResult:
        command = input.get("command")
        if not isinstance(command, str) or not command:
            return ToolExecutionResult(tool_use_id, "Bash: missing string 'command'", is_error=True)
        timeout_value = input.get("timeout", _DEFAULT_TIMEOUT)
        timeout = (
            float(timeout_value) if isinstance(timeout_value, (int, float)) else _DEFAULT_TIMEOUT
        )
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolExecutionResult(
                tool_use_id, f"Bash: command timed out after {timeout}s", is_error=True
            )
        except OSError as exc:
            return ToolExecutionResult(tool_use_id, f"Bash: {exc}", is_error=True)
        output = (proc.stdout or "") + (proc.stderr or "")
        if len(output) > _MAX_OUTPUT_CHARS:
            output = (
                output[:_MAX_OUTPUT_CHARS]
                + f"\n...[truncated {len(output) - _MAX_OUTPUT_CHARS} chars]"
            )
        if proc.returncode != 0:
            return ToolExecutionResult(
                tool_use_id, f"(exit {proc.returncode})\n{output}", is_error=True
            )
        return ToolExecutionResult(tool_use_id, output)
