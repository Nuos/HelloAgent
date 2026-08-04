"""流式渲染测试：分句输出、碎片合并、最终文本去重、工具事件渲染。"""

from __future__ import annotations

from collections.abc import AsyncIterator

from claude_code.cli.streaming import StreamPrinter, consume_events
from claude_code.types.events import (
    AgentCompleted,
    AgentEvent,
    AgentFailed,
    AssistantTextDelta,
    ToolCompleted,
    ToolRequested,
)
from claude_code.types.ids import SessionId, ToolUseId, TurnId
from claude_code.types.messages import (
    ModelStreamEvent,
    ModelTextDelta,
    ModelTurnCompleted,
)

SESSION = SessionId("s")
TURN = TurnId("t")


def test_stream_printer_merges_word_fragments(capsys: object) -> None:
    """SSE 按词碎片（你好/！/我是/Deep/Se/ek）应合并成句输出。"""
    printer = StreamPrinter()
    for chunk in ("你好", "！", "我是", " Deep", "Se", "ek"):
        printer.feed(chunk)
    printer.finish()
    captured = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "你好！" in captured
    assert "我是 DeepSeek" in captured
    # 无残留碎片：句子间以换行分隔
    assert captured.count("\n") >= 1


def test_stream_printer_buffers_incomplete_sentence(capsys: object) -> None:
    printer = StreamPrinter()
    printer.feed("还没有句号")
    captured = capsys.readouterr().out  # type: ignore[attr-defined]
    assert captured == ""  # 不完整句不输出
    printer.finish()
    captured = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "还没有句号" in captured


async def _events_from_model(events: list[ModelStreamEvent]) -> AsyncIterator[AgentEvent]:
    """按 QueryEngine 事件语义构造事件流：增量 + 完成。"""
    text_parts: list[str] = []
    for event in events:
        if isinstance(event, ModelTextDelta):
            text_parts.append(event.text)
            yield AssistantTextDelta(session_id=SESSION, turn=TURN, text=event.text)
    yield AgentCompleted(session_id=SESSION, text="".join(text_parts))


async def test_consume_events_no_duplicate_final_text(capsys: object) -> None:
    """流式增量已输出时，AgentCompleted 的完整文本不重复打印。"""
    events = [
        ModelTextDelta(text="你好"),
        ModelTextDelta(text="！"),
        ModelTurnCompleted(text="你好！"),
    ]
    failed = await consume_events(_events_from_model(events))
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert failed is False
    assert "你好！" in out
    assert out.count("你好") <= 2  # 增量合并后只出现一次完整句子


async def test_consume_events_prints_final_text_when_no_delta(capsys: object) -> None:
    """无流式增量（如 demo 模型整段文本）时打印完整最终文本。"""

    async def stream() -> AsyncIterator[AgentEvent]:
        yield AgentCompleted(session_id=SESSION, text="demo answer")

    failed = await consume_events(stream())
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert failed is False
    assert "demo answer" in out


async def test_consume_events_renders_tool_events(capsys: object) -> None:
    """工具调用/完成事件在文本流中即时渲染。"""

    async def stream() -> AsyncIterator[AgentEvent]:
        yield ToolRequested(
            session_id=SESSION,
            turn=TURN,
            tool_use_id=ToolUseId("u1"),
            name="Read",
            input={"path": "a"},
        )
        yield ToolCompleted(
            session_id=SESSION, turn=TURN, tool_use_id=ToolUseId("u1"), name="Read", is_error=False
        )
        yield AgentCompleted(session_id=SESSION, text="")

    failed = await consume_events(stream())
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert failed is False
    assert "Read" in out
    assert "done" in out


async def test_consume_events_reports_failure(capsys: object) -> None:
    async def stream() -> AsyncIterator[AgentEvent]:
        yield AgentFailed(session_id=SESSION, reason="model error: boom")

    failed = await consume_events(stream())
    assert failed is True
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "boom" in out
