"""REPL 测试：跨轮上下文累积、退出命令、EOF、命令分发、横幅提示。"""

from __future__ import annotations

import contextlib
import io
from collections.abc import AsyncIterator, Sequence
from pathlib import Path

from claude_code.commands import build_registry
from claude_code.replLauncher import run_repl
from claude_code.services.api.config import ApiConfig
from claude_code.services.api.demo import DemoModelClient
from claude_code.Tool import ToolSpec
from claude_code.types.messages import (
    Message,
    ModelStreamEvent,
    ModelTurnCompleted,
)


class CountingModel:
    """记录每次调用收到的消息链长度，验证跨轮上下文累积。"""

    name = "counting"

    def __init__(self) -> None:
        self.seen_message_counts: list[int] = []

    async def stream(
        self,
        messages: Sequence[Message],
        tool_specs: Sequence[ToolSpec],
    ) -> AsyncIterator[ModelStreamEvent]:
        self.seen_message_counts.append(len(messages))
        yield ModelTurnCompleted(text=f"turn-{len(self.seen_message_counts)}")


def _fake_input(queue: list[str]):
    def read(prompt: str) -> str:
        if not queue:
            raise EOFError
        return queue.pop(0)

    return read


async def _run_repl_with(
    root: Path,
    inputs: list[str],
    model: object,
) -> tuple[int, str]:
    """运行 REPL，返回 (退出码, 全部 stdout)。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = await run_repl(
            workspace_root=root,
            enable_bash=False,
            max_turns=10,
            model=model,  # type: ignore[arg-type]
            command_registry=build_registry(),
            prompt_fn=_fake_input(inputs),
        )
    return code, buf.getvalue()


def _api_config(api_key: str) -> ApiConfig:
    return ApiConfig(
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
    )


async def test_repl_accumulates_context_across_turns(tmp_path: Path) -> None:
    """连续输入两轮，第二轮模型应看到第一轮的 user+assistant 消息。"""
    model = CountingModel()
    code, _ = await _run_repl_with(tmp_path, ["first", "second", "/exit"], model)
    assert code == 0
    assert len(model.seen_message_counts) == 2
    assert model.seen_message_counts[1] > model.seen_message_counts[0]


async def test_repl_exit_command_returns_zero(tmp_path: Path) -> None:
    model = CountingModel()
    code, _ = await _run_repl_with(tmp_path, ["hello", "/exit"], model)
    assert code == 0
    assert len(model.seen_message_counts) == 1


async def test_repl_eof_terminates_cleanly(tmp_path: Path) -> None:
    code, _ = await _run_repl_with(tmp_path, [], CountingModel())
    assert code == 0


async def test_repl_dispatches_help_without_query(tmp_path: Path) -> None:
    model = CountingModel()
    code, _ = await _run_repl_with(tmp_path, ["/help", "/exit"], model)
    assert code == 0
    assert len(model.seen_message_counts) == 0


async def test_repl_banner_shows_model_name(tmp_path: Path) -> None:
    _, output = await _run_repl_with(tmp_path, ["/exit"], CountingModel())
    assert "模型: counting" in output.splitlines()[0]


async def test_repl_banner_hints_real_model_when_configured(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "claude_code.replLauncher.resolve_api_config",
        lambda: _api_config("sk-configured"),
    )
    _, output = await _run_repl_with(tmp_path, ["/exit"], DemoModelClient())
    banner = output.splitlines()[0]
    assert "检测到真实模型配置（deepseek-v4-flash）" in banner
    assert "/model openai" in banner


async def test_repl_banner_no_hint_without_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "claude_code.replLauncher.resolve_api_config",
        lambda: _api_config(""),
    )
    _, output = await _run_repl_with(tmp_path, ["/exit"], DemoModelClient())
    banner = output.splitlines()[0]
    assert "检测到真实模型配置" not in banner


class FakeOpenAIModel(CountingModel):
    """替代 _build_openai_model 返回的假真实模型。"""

    name = "openai:fake-model"


async def test_repl_model_switch_to_openai(tmp_path: Path, monkeypatch) -> None:
    fake = FakeOpenAIModel()
    monkeypatch.setattr("claude_code.replLauncher._build_openai_model", lambda: fake)
    initial = CountingModel()
    code, output = await _run_repl_with(tmp_path, ["/model openai", "hi", "/exit"], initial)
    assert code == 0
    assert "已切换模型: openai:fake-model" in output
    assert fake.seen_message_counts == [1]
    assert initial.seen_message_counts == []


async def test_repl_model_switch_back_to_demo(tmp_path: Path, monkeypatch) -> None:
    fake = FakeOpenAIModel()
    monkeypatch.setattr("claude_code.replLauncher._build_openai_model", lambda: fake)
    model = CountingModel()
    code, output = await _run_repl_with(
        tmp_path, ["/model openai", "/model demo", "hi", "/exit"], model
    )
    assert code == 0
    assert "已切换模型: openai:fake-model" in output
    assert "已切换模型: demo" in output
    # hi 由 DemoModelClient 处理（输出 [demo] received），初始 counting 模型未被调用
    assert model.seen_message_counts == []


async def test_repl_model_invalid_usage_prints_help(tmp_path: Path) -> None:
    code, output = await _run_repl_with(tmp_path, ["/model", "/exit"], CountingModel())
    assert code == 0
    assert "用法: /model demo（离线） 或 /model openai（真实模型）" in output
