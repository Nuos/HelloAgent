"""API 配置解析测试：配置文件读取、--config 覆盖、缺 key 引导。"""

from __future__ import annotations

import json

from claude_code.services.api.config import (
    create_config_guide,
    resolve_api_config,
)


def _write_config(path: object, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")  # type: ignore[union-attr]


def test_resolves_from_default_config(tmp_path: object) -> None:
    config_file = tmp_path / "c.json"  # type: ignore[union-attr]
    _write_config(
        config_file,
        {
            "api_key": "sk-test",
            "api_base": "https://api.deepseek.com",
            "model": "deepseek-chat",
        },
    )
    resolved = resolve_api_config(config_path=str(config_file))
    assert resolved.api_key == "sk-test"
    assert resolved.base_url == "https://api.deepseek.com"
    assert resolved.model == "deepseek-chat"
    assert resolved.timeout == 120


def test_cli_args_override_config(tmp_path: object) -> None:
    config_file = tmp_path / "c.json"  # type: ignore[union-attr]
    _write_config(config_file, {"api_key": "sk-file", "model": "m-file"})
    resolved = resolve_api_config(api_key="sk-cli", llm_model="m-cli", config_path=str(config_file))
    assert resolved.api_key == "sk-cli"
    assert resolved.model == "m-cli"


def test_timeout_from_config_and_override(tmp_path: object) -> None:
    config_file = tmp_path / "c.json"  # type: ignore[union-attr]
    _write_config(config_file, {"api_key": "k", "timeout": 60})
    assert resolve_api_config(config_path=str(config_file)).timeout == 60
    assert resolve_api_config(timeout=30, config_path=str(config_file)).timeout == 30


def test_missing_config_yields_defaults_and_empty_key(tmp_path: object) -> None:
    missing = tmp_path / "missing.json"  # type: ignore[union-attr]
    resolved = resolve_api_config(config_path=str(missing))
    assert resolved.api_key == ""
    assert resolved.base_url == "https://api.deepseek.com"


def test_create_config_guide_mentions_chmod() -> None:
    guide = create_config_guide()
    assert "~/.hellollm/config.json" in guide
    assert "chmod 600" in guide


def test_config_load_emits_logs(caplog: object, tmp_path: object) -> None:
    """配置加载/读取产生日志（key 打码），供 VS Code 调试排查。"""
    import logging

    config_file = tmp_path / "c.json"  # type: ignore[union-attr]
    _write_config(config_file, {"api_key": "sk-abc123", "model": "m1"})
    with caplog.at_level(logging.INFO, logger="claude_code.config"):  # type: ignore[attr-defined]
        resolve_api_config(config_path=str(config_file))
    messages = [r.message for r in caplog.records]  # type: ignore[attr-defined]
    assert any("配置文件已加载" in m for m in messages)
    # key 打码：前 4 位可见，完整 key 绝不出现
    assert any("sk-a" in m for m in messages)
    assert all("sk-abc123" not in m for m in messages)


def test_config_missing_emits_warning(caplog: object, tmp_path: object) -> None:
    import logging

    missing = tmp_path / "missing.json"  # type: ignore[union-attr]
    with caplog.at_level(logging.WARNING, logger="claude_code.config"):  # type: ignore[attr-defined]
        resolve_api_config(config_path=str(missing))
    messages = [r.message for r in caplog.records]  # type: ignore[attr-defined]
    assert any("配置文件不存在" in m for m in messages)
