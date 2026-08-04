"""help 命令：列出可用命令与工具，对应源码 commands/help。"""

from __future__ import annotations


def run_help(args: list[str]) -> str:
    """返回命令与工具使用说明。"""
    return (
        "Claude Code Python (R1)\n"
        "命令: /help, /init\n"
        "工具(经模型调用): /read <path>, /write <path> <content>, "
        "/edit <path> <old> <new>, /bash <command>(--enable-bash), "
        "/glob <pattern>, /grep <pattern> [path]\n"
        "示例: python -m claude_code hello | python -m claude_code '/read README.md'"
    )
