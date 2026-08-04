"""QueryEngine：核心查询循环，对应源码 QueryEngine.ts / queryLoop。

输入：UserRequest。输出：AgentEvent 异步流（模型增量、工具生命周期、完成/失败）。
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from claude_code.query.config import QueryConfig
from claude_code.query.deps import QueryDeps
from claude_code.state.store import Session
from claude_code.tools.registry import ToolRegistry
from claude_code.types.command import UserRequest
from claude_code.types.events import (
    AgentCompleted,
    AgentEvent,
    AgentFailed,
    AssistantTextDelta,
    ModelTurnStarted,
    ToolCompleted,
    ToolRequested,
    UserMessageAccepted,
)
from claude_code.types.ids import ToolUseId, TurnId
from claude_code.types.messages import (
    Message,
    ModelTextDelta,
    ModelTurnCompleted,
    Role,
    ToolResult,
)


class QueryEngine:
    """查询循环：装配上下文、调用模型、路由工具、回灌结果、判断停止。

    状态：Session 消息链与 turn_count；每轮整体替换可见消息。
    边界：不导入具体模型 SDK；工具一律经 ToolRegistry 执行。
    """

    def __init__(
        self,
        session: Session,
        registry: ToolRegistry,
        config: QueryConfig,
        deps: QueryDeps,
    ) -> None:
        self.session = session
        self.registry = registry
        self.config = config
        self.deps = deps

    def _new_turn_id(self) -> TurnId:
        return TurnId(self.deps.uuid())

    def _new_tool_use_id(self, name: str) -> ToolUseId:
        return ToolUseId(f"{self.deps.uuid()}-{name}")

    async def run(self, user_request: UserRequest) -> AsyncIterator[AgentEvent]:
        """执行一次完整查询，产出事件流直到完成或失败。"""
        session = self.session
        user_message = Message(role=Role.USER, content=user_request.text)
        session.append(user_message)
        yield UserMessageAccepted(session_id=session.session_id, message=user_message)

        while True:
            if session.turn_count >= self.config.max_turns:
                yield AgentFailed(
                    session_id=session.session_id,
                    reason=f"max_turns ({self.config.max_turns}) reached",
                )
                return

            session.turn_count += 1
            turn = self._new_turn_id()
            yield ModelTurnStarted(session_id=session.session_id, turn=turn)

            completed: ModelTurnCompleted | None = None
            collected: list[str] = []
            try:
                async for event in self.deps.call_model(
                    tuple(session.messages), self.registry.specs()
                ):
                    if isinstance(event, ModelTextDelta):
                        collected.append(event.text)
                        yield AssistantTextDelta(
                            session_id=session.session_id, turn=turn, text=event.text
                        )
                    elif isinstance(event, ModelTurnCompleted):
                        completed = event
            except Exception as exc:
                yield AgentFailed(
                    session_id=session.session_id,
                    reason=f"model error: {exc}",
                )
                return

            if completed is None:
                yield AgentFailed(
                    session_id=session.session_id,
                    reason="model stream ended without ModelTurnCompleted",
                )
                return

            if not completed.tool_calls:
                session.append(Message(role=Role.ASSISTANT, content=completed.text))
                yield AgentCompleted(session_id=session.session_id, text=completed.text)
                return

            session.append(
                Message(
                    role=Role.ASSISTANT,
                    content=completed.text,
                    tool_calls=completed.tool_calls,
                )
            )
            for tool_call in completed.tool_calls:
                yield ToolRequested(
                    session_id=session.session_id,
                    turn=turn,
                    tool_use_id=tool_call.id,
                    name=tool_call.name,
                    input=tool_call.input,
                )
                result = self.registry.execute(tool_call.name, tool_call.input, tool_call.id)
                yield ToolCompleted(
                    session_id=session.session_id,
                    turn=turn,
                    tool_use_id=tool_call.id,
                    name=tool_call.name,
                    is_error=result.is_error,
                )
                session.append(
                    Message(
                        role=Role.TOOL,
                        tool_result=ToolResult(
                            tool_use_id=tool_call.id,
                            content=result.content,
                            is_error=result.is_error,
                        ),
                    )
                )
