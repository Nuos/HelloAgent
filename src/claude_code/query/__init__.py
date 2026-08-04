"""查询入口，对应源码 query.ts（query() 包装，委托 QueryEngine）。

输入：请求、会话、工具池、配置。输出：AgentEvent 异步流。
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from claude_code.query.config import QueryConfig
from claude_code.query.deps import QueryDeps
from claude_code.state.store import Session
from claude_code.tools.registry import ToolRegistry
from claude_code.types.command import UserRequest
from claude_code.types.events import AgentEvent


async def query(
    user_request: UserRequest,
    session: Session,
    registry: ToolRegistry,
    config: QueryConfig,
    deps: QueryDeps,
) -> AsyncIterator[AgentEvent]:
    """构建 QueryEngine 并产出其事件流。

    函数内延迟导入 QueryEngine，避免与 QueryEngine.py 的循环导入。
    """
    from claude_code.QueryEngine import QueryEngine

    engine = QueryEngine(session, registry, config, deps)
    async for event in engine.run(user_request):
        yield event
