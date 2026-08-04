"""CLI 测试：参数解析、命令分发、事件渲染。"""

from __future__ import annotations

from claude_code.cli.parser import build_parser
from claude_code.cli.renderer import render_event
from claude_code.commands import build_registry
from claude_code.types.command import UserRequest
from claude_code.types.events import (
    AgentCompleted,
    AssistantTextDelta,
    ToolRequested,
)
from claude_code.types.ids import SessionId, ToolUseId, TurnId


def test_parser_defaults_to_bash_disabled() -> None:
    args = build_parser().parse_args(["hello"])
    assert args.enable_bash is False
    assert args.max_turns == 10


def test_parser_accepts_enable_bash() -> None:
    args = build_parser().parse_args(["--enable-bash", "pwd"])
    assert args.enable_bash is True


def test_user_request_parses_slash_command() -> None:
    request = UserRequest.create("/read README.md")
    assert request.command == "read"
    assert request.args == ["README.md"]


def test_user_request_plain_text() -> None:
    request = UserRequest.create("hello")
    assert request.command is None


def test_registry_only_has_help_and_init() -> None:
    registry = build_registry()
    assert "help" in registry.names()
    assert "init" in registry.names()


def test_render_event_preserves_text_delta() -> None:
    event = AssistantTextDelta(session_id=SessionId("s"), turn=TurnId("t"), text="chunk")
    assert render_event(event) == "chunk"


def test_render_event_tool_request() -> None:
    event = ToolRequested(
        session_id=SessionId("s"),
        turn=TurnId("t"),
        tool_use_id=ToolUseId("u"),
        name="Read",
        input={"path": "a.txt"},
    )
    rendered = render_event(event)
    assert rendered is not None and "Read" in rendered


def test_render_agent_completed_prints_final_text() -> None:
    event = AgentCompleted(session_id=SessionId("s"), text="done")
    assert render_event(event) == "\ndone"
