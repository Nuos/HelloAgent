"""交互式 REPL 入口，对应源码 replLauncher.tsx。

输入：stdin 逐行。输出：多轮查询的事件渲染（Session 跨轮保持上下文）。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from claude_code.cli.streaming import consume_events
from claude_code.commands import CommandRegistry
from claude_code.query import query
from claude_code.query.config import QueryConfig
from claude_code.query.deps import QueryDeps
from claude_code.services.api.claude import ModelClient, OpenAICompatibleClient
from claude_code.services.api.config import (
    create_config_guide,
    resolve_api_config,
)
from claude_code.services.api.demo import DemoModelClient
from claude_code.state.store import Session
from claude_code.tools import assemble_tool_pool
from claude_code.types.command import UserRequest
from claude_code.types.ids import SessionId

logger = logging.getLogger("claude_code.repl")

_EXIT_COMMANDS = ("/exit", "/quit")


def _real_model_hint() -> str:
    """检测 ~/.hellollm/config.json 是否可用，返回横幅提示。"""
    config = resolve_api_config()
    if config.api_key:
        return f" | 检测到真实模型配置（{config.model}）：输入 /model openai 切换"
    return ""


def _build_openai_model() -> ModelClient | None:
    """按配置文件构造真实模型客户端；缺 key 返回 None 并打印引导。"""
    config = resolve_api_config()
    if not config.api_key:
        logger.error("构造真实模型失败：未找到 API key（%s）", config.source)
        print("未找到 API key，请先创建 ~/.hellollm/config.json（chmod 600）")
        print(create_config_guide())
        return None
    logger.info(
        "构造真实模型客户端: model=%s base=%s key=%s...",
        config.model,
        config.base_url,
        config.api_key[:4],
    )
    return OpenAICompatibleClient(
        config.api_key, config.base_url, config.model, timeout=config.timeout
    )


async def run_repl(
    workspace_root: Path,
    enable_bash: bool,
    max_turns: int,
    model: ModelClient,
    command_registry: CommandRegistry,
    session_id: SessionId | None = None,
    prompt_fn: Callable[[str], str] | None = None,
) -> int:
    """运行交互式 REPL。

    输入：模型与配置。输出：退出码（正常退出 0，AgentFailed 计数作为失败返回）。
    会话保持：所有轮次共享同一 Session，上下文跨轮累积。
    """
    registry = assemble_tool_pool(workspace_root, enable_bash=enable_bash)
    session = Session(session_id=session_id or SessionId(model.name))
    current_model: ModelClient = model
    config = QueryConfig(
        session_id=session.session_id,
        max_turns=max_turns,
        model_name=current_model.name,
    )

    read_line = prompt_fn if prompt_fn is not None else input
    print(
        f"Claude Code Python REPL — 模型: {current_model.name} | /help 查看命令，/exit 退出"
        f"{_real_model_hint()}"
    )
    failures = 0
    while True:
        try:
            raw = read_line(">>> ")
        except EOFError:
            break
        line = str(raw).strip()
        if not line:
            continue
        if line in _EXIT_COMMANDS:
            break
        if line.startswith("/model"):
            parts = line.split()
            if len(parts) != 2 or parts[1] not in ("demo", "openai"):
                print("用法: /model demo（离线） 或 /model openai（真实模型）")
                continue
            if parts[1] == "openai":
                new_model = _build_openai_model()
                if new_model is None:
                    continue
            else:
                new_model = DemoModelClient()
            current_model = new_model
            config = QueryConfig(
                session_id=session.session_id,
                max_turns=max_turns,
                model_name=current_model.name,
            )
            print(f"已切换模型: {current_model.name}")
            continue
        if line.startswith("/"):
            output = command_registry.run(line[1:].split()[0], line[1:].split()[1:])
            if output is not None:
                print(output)
                continue
        deps = QueryDeps(call_model=current_model.stream)
        events = query(UserRequest.create(line), session, registry, config, deps)
        if await consume_events(events):
            failures += 1
    return 1 if failures else 0
