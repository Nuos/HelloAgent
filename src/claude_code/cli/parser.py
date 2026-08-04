"""CLI 参数解析，对应源码 cli 层的 parser 概念。

输入：argv。输出：argparse.Namespace（prompt、--enable-bash、--max-turns、--cwd）。
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="claude_code",
        description="Claude Code 类 Agent（Python 教学实现）",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="任务文本或 slash 命令，如 hello 或 /read README.md",
    )
    parser.add_argument(
        "--enable-bash",
        action="store_true",
        help="显式启用 Bash 工具（默认不注册）",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="最大模型轮次（默认 10）",
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="工作区根目录（默认当前目录）",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="进入交互式 REPL（多轮对话）",
    )
    parser.add_argument(
        "--model",
        default="demo",
        choices=["demo", "openai"],
        help="模型后端：demo（离线替身）或 openai（兼容 API）",
    )
    parser.add_argument("--api-key", default=None, help="真实模型 API key")
    parser.add_argument("--api-base", default=None, help="真实模型 base URL")
    parser.add_argument("--llm-model", default=None, help="真实模型的模型名")
    parser.add_argument(
        "--config",
        default=None,
        help="API 配置文件路径（默认 ~/.hellollm/config.json）",
    )
    parser.add_argument("--timeout", type=int, default=None, help="API 请求超时秒数")
    return parser
