"""命令注册表，对应源码 commands.ts 与 commands/ 目录。

输入：命令名与参数。输出：命令执行文本；未注册命令返回 None。
"""

from __future__ import annotations

from collections.abc import Callable

CommandHandler = Callable[[list[str]], str]


class CommandRegistry:
    """按名称注册与分发用户命令。"""

    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, name: str, handler: CommandHandler) -> None:
        """注册命令处理器。"""
        self._handlers[name] = handler

    def names(self) -> tuple[str, ...]:
        """已注册命令名列表。"""
        return tuple(self._handlers.keys())

    def run(self, name: str, args: list[str]) -> str | None:
        """执行命令；未注册返回 None。"""
        handler = self._handlers.get(name)
        return None if handler is None else handler(args)


def build_registry() -> CommandRegistry:
    """装配内置命令：help 与 init。"""
    from claude_code.commands.help import run_help
    from claude_code.commands.init import run_init

    registry = CommandRegistry()
    registry.register("help", run_help)
    registry.register("init", run_init)
    return registry
