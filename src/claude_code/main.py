"""CLI 入口，对应源码 main.tsx。

输入：argv。输出：退出码（0 成功 / 1 失败）。
无参数或 -i 进入交互式 REPL；--model openai 使用真实模型后端。
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from uuid import uuid4

from claude_code.cli.exit import EXIT_FAILURE, EXIT_SUCCESS
from claude_code.cli.parser import build_parser
from claude_code.cli.streaming import consume_events
from claude_code.commands import CommandRegistry, build_registry
from claude_code.query import query
from claude_code.query.config import QueryConfig
from claude_code.query.deps import QueryDeps
from claude_code.replLauncher import run_repl
from claude_code.services.api.claude import ModelClient, OpenAICompatibleClient
from claude_code.services.api.config import create_config_guide, resolve_api_config
from claude_code.services.api.demo import DemoModelClient
from claude_code.state.store import Session
from claude_code.tools import assemble_tool_pool
from claude_code.types.command import UserRequest
from claude_code.types.ids import SessionId


def _build_model(args: object) -> ModelClient:
    """按参数构造模型客户端：demo 离线替身或 openai 兼容 API。"""
    if args.model == "openai":  # type: ignore[attr-defined]
        config = resolve_api_config(
            api_key=args.api_key,  # type: ignore[attr-defined]
            api_base=args.api_base,  # type: ignore[attr-defined]
            llm_model=args.llm_model,  # type: ignore[attr-defined]
            timeout=args.timeout,  # type: ignore[attr-defined]
            config_path=args.config,  # type: ignore[attr-defined]
        )
        if not config.api_key:
            print(
                "错误: 未找到 API key（--api-key 或配置文件）",
                file=sys.stderr,
            )
            print(create_config_guide(), file=sys.stderr)
            raise SystemExit(EXIT_FAILURE)
        return OpenAICompatibleClient(
            config.api_key, config.base_url, config.model, timeout=config.timeout
        )
    return DemoModelClient()


async def _run_query(
    prompt: str,
    workspace_root: Path,
    enable_bash: bool,
    max_turns: int,
    model: ModelClient,
) -> int:
    """运行一次完整查询并渲染事件；AgentFailed 时返回失败码。"""
    registry = assemble_tool_pool(workspace_root, enable_bash=enable_bash)
    session_id = SessionId(uuid4().hex)
    session = Session(session_id=session_id)
    config = QueryConfig(session_id=session_id, max_turns=max_turns, model_name=model.name)
    deps = QueryDeps(call_model=model.stream)
    request = UserRequest.create(prompt)

    failed = await consume_events(query(request, session, registry, config, deps))
    return EXIT_FAILURE if failed else EXIT_SUCCESS


def _run_command(registry: CommandRegistry, prompt: str) -> str | None:
    """分发注册命令；非命令返回 None。"""
    if not prompt.startswith("/"):
        return None
    name, _, rest = prompt[1:].partition(" ")
    return registry.run(name, rest.split())


def main(argv: list[str] | None = None) -> int:
    """程序入口：无参数进 REPL，有参数执行单次查询或命令。"""
    logging.basicConfig(
        level=logging.INFO,
        format="[config] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    prompt = " ".join(args.prompt) if args.prompt else ""
    workspace_root = Path(args.cwd).resolve() if args.cwd else Path.cwd().resolve()

    if not prompt or args.interactive:
        return asyncio.run(
            run_repl(
                workspace_root=workspace_root,
                enable_bash=args.enable_bash,
                max_turns=args.max_turns,
                model=_build_model(args),
                command_registry=build_registry(),
            )
        )

    command_registry = build_registry()
    command_output = _run_command(command_registry, prompt)
    if command_output is not None:
        print(command_output)
        return EXIT_SUCCESS

    return asyncio.run(
        _run_query(
            prompt,
            workspace_root,
            args.enable_bash,
            args.max_turns,
            _build_model(args),
        )
    )


if __name__ == "__main__":
    sys.exit(main())
