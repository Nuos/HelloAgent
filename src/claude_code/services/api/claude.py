"""模型 API 适配层，对应源码 services/api/claude.js（queryModelWithStreaming）。

输入：消息序列与工具规格。输出：ModelStreamEvent 异步流。
包含 ModelClient 边界协议与 OpenAI 兼容 API 客户端（aihub.top / deepseek / openai）。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from typing import Any, Protocol

import httpx

from claude_code.Tool import ToolSpec
from claude_code.types.ids import ToolUseId
from claude_code.types.messages import (
    Message,
    ModelStreamEvent,
    ModelTextDelta,
    ModelTurnCompleted,
    Role,
    ToolCall,
)


class ModelClientError(RuntimeError):
    """模型 API 调用失败（网络、鉴权、协议错误）。"""


class ModelClient(Protocol):
    """模型客户端边界协议。

    stream 产出 ModelTextDelta 增量与最终 ModelTurnCompleted；
    具体模型 SDK 禁止直接访问工作区。
    """

    name: str

    def stream(
        self,
        messages: Sequence[Message],
        tool_specs: Sequence[ToolSpec],
    ) -> AsyncIterator[ModelStreamEvent]: ...


def message_to_openai(message: Message) -> dict[str, Any]:
    """把内部 Message 转为 OpenAI messages 格式。

    输入：Message。输出：dict；tool 消息携带 tool_call_id，assistant 消息携带 tool_calls。
    """
    if message.role is Role.USER:
        return {"role": "user", "content": message.content}
    if message.role is Role.ASSISTANT:
        item: dict[str, Any] = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            item["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.input, ensure_ascii=False),
                    },
                }
                for tc in message.tool_calls
            ]
        return item
    if message.role is Role.TOOL:
        result = message.tool_result
        assert result is not None, "tool 消息缺少 tool_result"
        return {
            "role": "tool",
            "tool_call_id": result.tool_use_id,
            "content": result.content,
        }
    return {"role": "system", "content": message.content}


def tool_to_openai(spec: ToolSpec) -> dict[str, Any]:
    """把 ToolSpec 转为 OpenAI tools 格式。"""
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": spec.input_schema,
        },
    }


class OpenAICompatibleClient:
    """OpenAI 兼容 chat/completions 流式客户端（含工具调用）。

    输入：api_key、base_url、model 与可选 httpx 客户端（测试可注入 MockTransport）。
    输出：ModelTextDelta 增量流与最终 ModelTurnCompleted。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int = 120,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = http_client or httpx.AsyncClient(timeout=httpx.Timeout(float(timeout)))
        self.name = f"openai:{model}"

    async def stream(
        self,
        messages: Sequence[Message],
        tool_specs: Sequence[ToolSpec],
    ) -> AsyncIterator[ModelStreamEvent]:
        """流式调用 /chat/completions 并解析 SSE 增量。"""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [message_to_openai(m) for m in messages],
            "stream": True,
        }
        if tool_specs:
            payload["tools"] = [tool_to_openai(spec) for spec in tool_specs]
            payload["tool_choice"] = "auto"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        text_parts: list[str] = []
        tool_calls_agg: dict[int, dict[str, str]] = {}
        try:
            async with self._client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="replace")
                    raise ModelClientError(f"API {resp.status_code}: {body[:300]}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        text_parts.append(content)
                        yield ModelTextDelta(text=content)
                    for tool_call in delta.get("tool_calls", []):
                        index = tool_call.get("index", 0)
                        agg = tool_calls_agg.setdefault(index, {"id": "", "name": "", "args": ""})
                        if tool_call.get("id"):
                            agg["id"] = tool_call["id"]
                        function = tool_call.get("function", {})
                        if function.get("name"):
                            agg["name"] = function["name"]
                        if function.get("arguments"):
                            agg["args"] += function["arguments"]
        except httpx.HTTPError as exc:
            raise ModelClientError(f"request failed: {exc}") from exc

        text = "".join(text_parts)
        if tool_calls_agg:
            calls = tuple(
                ToolCall(
                    id=ToolUseId(agg["id"] or f"call-{index}"),
                    name=agg["name"],
                    input=json.loads(agg["args"] or "{}"),
                )
                for index, agg in sorted(tool_calls_agg.items())
            )
            yield ModelTurnCompleted(text=text, tool_calls=calls)
        else:
            yield ModelTurnCompleted(text=text)
