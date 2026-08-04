"""API 服务子包：模型客户端、演示模型与配置解析，对应源码 services/api/。"""

from claude_code.services.api.claude import (
    ModelClient,
    ModelClientError,
    OpenAICompatibleClient,
    message_to_openai,
    tool_to_openai,
)
from claude_code.services.api.config import ApiConfig, resolve_api_config
from claude_code.services.api.demo import DemoModelClient

__all__ = [
    "ApiConfig",
    "DemoModelClient",
    "ModelClient",
    "ModelClientError",
    "OpenAICompatibleClient",
    "message_to_openai",
    "resolve_api_config",
    "tool_to_openai",
]
