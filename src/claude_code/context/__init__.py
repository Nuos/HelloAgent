"""上下文装配，对应源码 context.ts（getSystemContext/getUserContext）与 context/ 目录。

输入：项目根目录与配置。输出：系统上下文文本（环境信息）与用户上下文文本（CLAUDE.md）。
"""

from __future__ import annotations

from pathlib import Path

from claude_code.query.config import QueryConfig

_CLAUDE_MD_NAMES = ("CLAUDE.md", ".claude/CLAUDE.md")


def get_system_context(config: QueryConfig) -> str:
    """基础系统提示与环境信息。"""
    return f"{config.system_prompt}\nSession: {config.session_id}\nModel: {config.model_name}"


def load_claude_md(root: Path) -> str:
    """读取项目指令文件 CLAUDE.md；不存在时返回空串。"""
    for name in _CLAUDE_MD_NAMES:
        candidate = root / name
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return ""
    return ""


def get_user_context(root: Path) -> str:
    """用户上下文：CLAUDE.md 内容（含路径来源）。"""
    for name in _CLAUDE_MD_NAMES:
        candidate = root / name
        if candidate.is_file():
            content = load_claude_md(root)
            return f"# {name}\n{content}"
    return ""
