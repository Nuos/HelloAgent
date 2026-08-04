"""流式文本友好渲染：按句子边界输出，避免 SSE 按词碎片的乱格式。

输入：查询事件流。输出：分句友好的流式文本 + 工具事件渲染；
流式增量已输出时最终文本不重复打印。
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

from claude_code.cli.renderer import render_event
from claude_code.types.events import (
    AgentCompleted,
    AgentEvent,
    AgentFailed,
    AssistantTextDelta,
    ToolCompleted,
    ToolRequested,
)

_SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？；\n])")


class StreamPrinter:
    """缓冲文本增量，按句末标点/换行输出。

    输入：增量文本。输出：友好分段的流式文本；
    emitted 标记是否输出过增量（供最终文本去重）。
    """

    def __init__(self) -> None:
        self._buffer = ""
        self.emitted = False

    def feed(self, text: str) -> None:
        """追加增量并按句边界 flush；不完整句保留在缓冲。"""
        self._buffer += text
        segments = _SENTENCE_BOUNDARY.split(self._buffer)
        if len(segments) > 1:
            for segment in segments[:-1]:
                if segment:
                    print(segment, end="", flush=True)
                    self.emitted = True
            self._buffer = segments[-1]

    def finish(self) -> None:
        """flush 残留缓冲；保证本轮输出以换行结束。"""
        if self._buffer:
            print(self._buffer, flush=True)
            self.emitted = True
        elif self.emitted:
            print()
        self._buffer = ""


async def consume_events(stream: AsyncIterator[AgentEvent]) -> bool:
    """消费查询事件流并友好渲染；返回是否有 AgentFailed。

    文本增量经 StreamPrinter 分句输出；工具事件即时渲染；
    AgentCompleted 仅在未流式输出过增量时打印完整文本（去重）。
    """
    printer = StreamPrinter()
    failed = False
    async for event in stream:
        if isinstance(event, AssistantTextDelta):
            printer.feed(event.text)
        elif isinstance(event, ToolRequested):
            printer.finish()
            line = render_event(event)
            if line:
                print(line)
        elif isinstance(event, ToolCompleted):
            line = render_event(event)
            if line:
                print(line)
        elif isinstance(event, AgentFailed):
            printer.finish()
            failed = True
            line = render_event(event)
            if line:
                print(line)
        elif isinstance(event, AgentCompleted):
            had_delta = printer.emitted
            printer.finish()
            if not had_delta:
                line = render_event(event)
                if line:
                    print(line)
    return failed
