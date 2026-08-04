"""VS Code 配置文件结构测试：launch/tasks/settings 合法性与会话集成。

配置风格对齐 HelloLLM 项目：program 指向入口脚本、显式 venv python、
deepseek NO_PROXY env、集成终端自动激活 venv。
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VSCODE_DIR = PROJECT_ROOT / ".vscode"

_LAUNCH = json.loads((VSCODE_DIR / "launch.json").read_text(encoding="utf-8"))
_TASKS = json.loads((VSCODE_DIR / "tasks.json").read_text(encoding="utf-8"))
_SETTINGS = json.loads((VSCODE_DIR / "settings.json").read_text(encoding="utf-8"))


def test_all_vscode_json_are_valid() -> None:
    for name in ("launch.json", "tasks.json", "settings.json", "extensions.json"):
        json.loads((VSCODE_DIR / name).read_text(encoding="utf-8"))


def test_launch_has_two_repl_configs() -> None:
    names = [c["name"] for c in _LAUNCH["configurations"]]
    assert names == ["HelloAgent (REPL)", "HelloAgent (REPL Real Model)"]


def test_launch_uses_program_entry_like_hellollm() -> None:
    """对齐 HelloLLM：program 直接指向入口脚本 main.py。"""
    for config in _LAUNCH["configurations"]:
        assert config["program"] == "${workspaceFolder}/src/claude_code/main.py"
        assert config["cwd"] == "${workspaceFolder}"
        assert config["console"] == "integratedTerminal"


def test_launch_pins_venv_python_and_deepseek_no_proxy() -> None:
    """对齐 HelloLLM：显式解释器路径 + deepseek 直连绕过代理。"""
    for config in _LAUNCH["configurations"]:
        assert config["python"] == "${workspaceFolder}/.venv/bin/python"
        env = config.get("env", {})
        assert env.get("NO_PROXY") == "api.deepseek.com"
        assert env.get("no_proxy") == "api.deepseek.com"


def test_launch_real_model_config_uses_openai() -> None:
    config = next(
        c for c in _LAUNCH["configurations"] if c["name"] == "HelloAgent (REPL Real Model)"
    )
    assert config["args"] == ["--model", "openai"]


def test_tasks_has_bootstrap_and_quality_gate() -> None:
    labels = [t["label"] for t in _TASKS["tasks"]]
    assert "Bootstrap Python 3.14 Environment" in labels
    assert "Quality Gate" in labels


def test_quality_gate_covers_all_gates() -> None:
    task = next(t for t in _TASKS["tasks"] if t["label"] == "Quality Gate")
    command = task["command"]
    assert "pytest" in command
    assert "ruff check" in command
    assert "ruff format --check" in command
    assert "mypy src" in command


def test_settings_interpreter_points_to_venv() -> None:
    assert _SETTINGS["python.defaultInterpreterPath"] == ("${workspaceFolder}/.venv/bin/python")
    assert _SETTINGS["python.analysis.typeCheckingMode"] == "strict"


def test_settings_activate_environment_in_terminal() -> None:
    """对齐 HelloLLM：集成终端自动激活 venv。"""
    assert _SETTINGS.get("python.terminal.activateEnvironment") is True
    assert _SETTINGS.get("python.terminal.activateEnvInCurrentTerminal") is True


def test_extensions_recommend_python_toolchain() -> None:
    data = json.loads((VSCODE_DIR / "extensions.json").read_text(encoding="utf-8"))
    recommended = data["recommendations"]
    assert "ms-python.python" in recommended
    assert "ms-python.debugpy" in recommended
