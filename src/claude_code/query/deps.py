"""查询依赖注入，对应源码 query/deps.ts（QueryDeps）。

输入：可注入的模型调用函数与 UUID 生成器。输出：QueryDeps，供测试注入假实现。
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import dataclass, field
from uuid import uuid4

from claude_code.Tool import ToolSpec
from claude_code.types.messages import Message, ModelStreamEvent

ModelCallFn = Callable[[Sequence[Message], Sequence[ToolSpec]], AsyncIterator[ModelStreamEvent]]


@dataclass(slots=True)
class QueryDeps:
    """查询的 I/O 依赖；测试可替换 call_model 注入假模型。"""

    call_model: ModelCallFn
    uuid: Callable[[], str] = field(default_factory=lambda: lambda: uuid4().hex)
