"""API 配置解析，对照 HelloLLM utils/config.py 与源码 utils/config.ts 思路。

配置来源优先级：--config 指定文件 > ~/.hellollm/config.json（唯一本地来源）。
格式：{"api_key": "...", "api_base": "...", "model": "...", "timeout": 120}
创建后 chmod 600 仅本人可读。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("claude_code.config")

_DEFAULT_CONFIG_PATH = Path.home() / ".hellollm" / "config.json"
_DEFAULT_BASE_URL = "https://api.deepseek.com"
_DEFAULT_MODEL = "deepseek-chat"
_DEFAULT_TIMEOUT = 120


@dataclass(frozen=True, slots=True)
class ApiConfig:
    """解析后的 API 连接配置。"""

    api_key: str
    base_url: str
    model: str
    timeout: int = _DEFAULT_TIMEOUT
    source: str = ""


def _load_json(path: Path) -> dict[str, str]:
    """读取 JSON 配置文件；缺失或损坏返回空字典，并记录加载日志。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("配置文件不存在: %s", path)
        return {}
    except OSError as exc:
        logger.warning("配置文件读取失败: %s (%s)", path, exc)
        return {}
    except json.JSONDecodeError as exc:
        logger.warning("配置文件解析失败: %s (%s)", path, exc)
        return {}
    if not isinstance(data, dict):
        logger.warning("配置文件格式错误（顶层非对象）: %s", path)
        return {}
    loaded = {str(k): str(v) for k, v in data.items() if isinstance(v, (str, int, float))}
    logger.info("配置文件已加载: %s (字段: %s)", path, ",".join(sorted(loaded)))
    return loaded


def config_path_hint() -> str:
    """返回推荐配置文件路径（供缺 key 提示使用）。"""
    return str(_DEFAULT_CONFIG_PATH)


def create_config_guide() -> str:
    """缺 key 时的创建引导文本（对齐 HelloLLM 的提示方式）。"""
    return (
        f"请创建配置文件 {_DEFAULT_CONFIG_PATH}（chmod 600）：\n"
        "mkdir -p ~/.hellollm && cat > ~/.hellollm/config.json <<'EOF'\n"
        '{\n  "api_key": "sk-...",\n  "api_base": "https://api.deepseek.com",\n'
        '  "model": "deepseek-chat",\n  "timeout": 120\n}\n'
        "EOF\nchmod 600 ~/.hellollm/config.json"
    )


def resolve_api_config(
    api_key: str | None = None,
    api_base: str | None = None,
    llm_model: str | None = None,
    timeout: int | None = None,
    config_path: str | None = None,
) -> ApiConfig:
    """按优先级解析 API 配置。

    输入：可选覆盖值（--api-key/--api-base/--llm-model/--config）。
    输出：ApiConfig；主来源为配置文件（--config 指定或 ~/.hellollm/config.json），
    显式参数优先，其次环境变量（OPENAI_API_KEY/OPENAI_BASE_URL/OPENAI_MODEL）。
    """
    path = Path(config_path).expanduser() if config_path else _DEFAULT_CONFIG_PATH
    file_config = _load_json(path)

    key = api_key or os.environ.get("OPENAI_API_KEY") or file_config.get("api_key") or ""
    base = (
        api_base
        or os.environ.get("OPENAI_BASE_URL")
        or file_config.get("api_base")
        or _DEFAULT_BASE_URL
    )
    model = (
        llm_model or os.environ.get("OPENAI_MODEL") or file_config.get("model") or _DEFAULT_MODEL
    )
    timeout_value = timeout or int(file_config.get("timeout", _DEFAULT_TIMEOUT))
    if not key:
        logger.error("未找到 API key（配置文件: %s，env OPENAI_API_KEY 未设置）", path)
    else:
        logger.info(
            "API key 已加载: %s... (来源: %s, base=%s, model=%s)",
            key[:4],
            path,
            base,
            model,
        )
    return ApiConfig(
        api_key=key,
        base_url=base,
        model=model,
        timeout=timeout_value,
        source=str(path),
    )
