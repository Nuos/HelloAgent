"""QueryEngine 契约测试：文本路径、工具回灌、max_turns 终止。"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from uuid import uuid4

from claude_code.query.config import QueryConfig
from claude_code.query.deps import QueryDeps
from claude_code.QueryEngine import QueryEngine
from claude_code.services.api.demo import DemoModelClient
from claude_code.state.store import Session
from claude_code.Tool import ToolSpec
from claude_code.tools import assemble_tool_pool
from claude_code.types.command import UserRequest
from claude_code.types.events import (
    AgentCompleted,
    AgentEvent,
    AgentFailed,
    ToolCompleted,
    ToolRequested,
)
from claude_code.types.ids import SessionId, ToolUseId
from claude_code.types.messages import Message, ModelStreamEvent, ModelTurnCompleted, ToolCall


async def _collect(
    prompt: str,
    root: Path,
    enable_bash: bool = False,
    max_turns: int = 10,
) -> tuple[list[AgentEvent], Session]:
    registry = assemble_tool_pool(root, enable_bash=enable_bash)
    session = Session(session_id=SessionId(uuid4().hex))
    config = QueryConfig(session_id=session.session_id, max_turns=max_turns)
    model = DemoModelClient()
    deps = QueryDeps(call_model=model.stream)
    events: list[AgentEvent] = []
    async for event in QueryEngine(session, registry, config, deps).run(UserRequest.create(prompt)):
        events.append(event)
    return events, session


async def test_text_only_response_completes_in_one_turn(tmp_path: Path) -> None:
    events, session = await _collect("hello", tmp_path)
    assert any(isinstance(event, AgentCompleted) for event in events)
    assert not any(isinstance(event, AgentFailed) for event in events)
    assert session.turn_count == 1


async def test_read_tool_result_is_fed_back_to_second_turn(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("hello world", encoding="utf-8")
    events, session = await _collect("/read a.txt", tmp_path)
    tool_requests = [e for e in events if isinstance(e, ToolRequested)]
    assert len(tool_requests) == 1
    assert tool_requests[0].name == "Read"
    assert any(isinstance(event, AgentCompleted) for event in events)
    tool_msgs = [m for m in session.messages if m.is_tool_result]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].tool_result is not None
    assert "hello world" in tool_msgs[0].tool_result.content


async def test_unknown_tool_returns_structured_error(tmp_path: Path) -> None:
    """假模型第一轮产生未知工具调用，loop 应回灌结构化错误并以文本完成。"""

    async def unknown_tool_model(
        messages: Sequence[Message], tool_specs: Sequence[ToolSpec]
    ) -> AsyncIterator[ModelStreamEvent]:
        if not any(m.is_tool_result for m in messages):
            yield ModelTurnCompleted(
                text="",
                tool_calls=(ToolCall(id=ToolUseId("u1"), name="NoSuchTool", input={}),),
            )
        else:
            yield ModelTurnCompleted(text="done")

    registry = assemble_tool_pool(tmp_path)
    session = Session(session_id=SessionId(uuid4().hex))
    config = QueryConfig(session_id=session.session_id)
    deps = QueryDeps(call_model=unknown_tool_model)
    events: list[AgentEvent] = []
    async for event in QueryEngine(session, registry, config, deps).run(
        UserRequest.create("run it")
    ):
        events.append(event)
    tool_completed = [e for e in events if isinstance(e, ToolCompleted)]
    assert tool_completed and tool_completed[0].is_error
    assert any(isinstance(event, AgentCompleted) for event in events)


async def test_max_turns_terminates_with_agent_failed(tmp_path: Path) -> None:
    events, _ = await _collect("hello", tmp_path, max_turns=0)
    assert any(isinstance(event, AgentFailed) for event in events)


async def test_event_order_text_path(tmp_path: Path) -> None:
    events, _ = await _collect("hello", tmp_path)
    kinds = [type(event).__name__ for event in events]
    assert kinds[0] == "UserMessageAccepted"
    assert kinds[1] == "ModelTurnStarted"
    assert "AssistantTextDelta" in kinds
    assert kinds[-1] == "AgentCompleted"


async def test_edit_tool_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "b.txt"
    target.write_text("alpha beta gamma", encoding="utf-8")
    events, session = await _collect("/edit b.txt beta BETA", tmp_path)
    assert any(isinstance(event, ToolRequested) for event in events)
    tool_msgs = [m for m in session.messages if m.is_tool_result]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].tool_result is not None
    assert not tool_msgs[0].tool_result.is_error
    assert target.read_text(encoding="utf-8") == "alpha BETA gamma"


async def test_write_tool_round_trip(tmp_path: Path) -> None:
    events, _session = await _collect("/write new.txt hello world", tmp_path)
    assert any(isinstance(event, ToolRequested) for event in events)
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "hello world"
    assert any(isinstance(event, AgentCompleted) for event in events)
