"""CLI 层：参数解析、事件渲染、退出码，对应源码 cli/ 目录。

边界：解析与渲染，不直接执行工具或修改会话。
"""

from claude_code.cli.exit import EXIT_FAILURE, EXIT_SUCCESS
from claude_code.cli.parser import build_parser
from claude_code.cli.renderer import render_event

__all__ = ["EXIT_FAILURE", "EXIT_SUCCESS", "build_parser", "render_event"]
