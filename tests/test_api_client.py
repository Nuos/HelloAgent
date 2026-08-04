"""真实模型客户端测试：OpenAI 格式转换、SSE 流解析（假 HTTP）、错误转失败。"""

from __future__ import annotations

import json

import httpx
import pytest

from claude_code.services.api.claude import (
    ModelClientError,
    OpenAICompatibleClient,
    message_to_openai,
    tool_to_openai,
)
from claude_code.Tool import ToolSpec
from claude_code.types.ids import ToolUseId
from claude_code.types.messages import (
    Message,
    ModelStreamEvent,
    ModelTextDelta,
    ModelTurnCompleted,
    Role,
    ToolResult,
)


def test_message_to_openai_user() -> None:
    converted = message_to_openai(Message(role=Role.USER, content="hi"))
    assert converted == {"role": "user", "content": "hi"}


def test_message_to_openai_tool_result_carries_tool_call_id() -> None:
    message = Message(
        role=Role.TOOL,
        tool_result=ToolResult(tool_use_id=ToolUseId("call-1"), content="result"),
    )
    converted = message_to_openai(message)
    assert converted["tool_call_id"] == "call-1"
    assert converted["content"] == "result"


def test_message_to_openai_assistant_with_tool_calls() -> None:
    from claude_code.types.messages import ToolCall

    message = Message(
        role=Role.ASSISTANT,
        content="",
        tool_calls=(
            ToolCall(
                id=ToolUseId("call-9"),
                name="Read",
                input={"path": "a.txt"},
            ),
        ),
    )
    converted = message_to_openai(message)
    call = converted["tool_calls"][0]
    assert call["id"] == "call-9"
    assert call["function"]["name"] == "Read"
    assert json.loads(call["function"]["arguments"]) == {"path": "a.txt"}


def test_tool_to_openai() -> None:
    spec = ToolSpec(name="Read", description="read a file", input_schema={"type": "object"})
    converted = tool_to_openai(spec)
    assert converted["type"] == "function"
    assert converted["function"]["name"] == "Read"


def _sse_response(chunks: list[dict]) -> httpx.Response:
    """构造 SSE 流式响应体。"""
    lines: list[str] = []
    for chunk in chunks:
        lines.append(f"data: {json.dumps(chunk)}")
    lines.append("data: [DONE]")
    body = "\n".join(lines) + "\n"
    return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})


async def test_client_streams_text_deltas() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is True
        return _sse_response(
            [
                {"choices": [{"delta": {"content": "Hel"}}]},
                {"choices": [{"delta": {"content": "lo"}}]},
                {"choices": [{"delta": {}, "finish_reason": "stop"}]},
            ]
        )

    transport = httpx.MockTransport(handler)
    client = OpenAICompatibleClient(
        api_key="k",
        base_url="https://fake.test/v1",
        model="m",
        http_client=httpx.AsyncClient(transport=transport),
    )
    events: list[ModelStreamEvent] = []
    async for event in client.stream(
        [Message(role=Role.USER, content="hi")], [ToolSpec(name="Read")]
    ):
        events.append(event)
    text_deltas = [e for e in events if isinstance(e, ModelTextDelta)]
    assert "".join(e.text for e in text_deltas) == "Hello"
    completed = [e for e in events if isinstance(e, ModelTurnCompleted)]
    assert completed and completed[0].text == "Hello"
    assert not completed[0].tool_calls


async def test_client_merges_streamed_tool_calls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _sse_response(
            [
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "id": "call-1",
                                        "function": {"name": "Read", "arguments": ""},
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "choices": [
                        {"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"pa'}}]}}
                    ]
                },
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {"index": 0, "function": {"arguments": 'th": "a.txt"}'}}
                                ]
                            }
                        }
                    ]
                },
                {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]},
            ]
        )

    transport = httpx.MockTransport(handler)
    client = OpenAICompatibleClient(
        api_key="k",
        base_url="https://fake.test/v1",
        model="m",
        http_client=httpx.AsyncClient(transport=transport),
    )
    events: list[ModelStreamEvent] = []
    async for event in client.stream(
        [Message(role=Role.USER, content="read")], [ToolSpec(name="Read")]
    ):
        events.append(event)
    completed = [e for e in events if isinstance(e, ModelTurnCompleted)]
    assert completed and len(completed[0].tool_calls) == 1
    call = completed[0].tool_calls[0]
    assert call.name == "Read"
    assert call.input == {"path": "a.txt"}


async def test_client_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text='{"error": "bad key"}')

    transport = httpx.MockTransport(handler)
    client = OpenAICompatibleClient(
        api_key="bad",
        base_url="https://fake.test/v1",
        model="m",
        http_client=httpx.AsyncClient(transport=transport),
    )
    with pytest.raises(ModelClientError):
        async for _event in client.stream([Message(role=Role.USER, content="hi")], []):
            pass
