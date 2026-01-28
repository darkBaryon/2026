from __future__ import annotations

import os

from .base import BaseLLMClient
from .openai_client import OpenAIClient


def get_llm_client() -> BaseLLMClient:
    """
    简单的 LLM Client 工厂。

    通过环境变量 AI_PROVIDER 选择不同的实现：

    - openai（默认）: 使用 OpenAIClient
    - 未来你可以在这里扩展：
      - deepseek: DeepSeekClient
      - claude: ClaudeClient
      - internal: 内网模型客户端
    """
    provider = os.getenv("AI_PROVIDER", "openai").lower()

    if provider in {"openai", ""}:
        return OpenAIClient()

    # 目前还没有实现其他 Provider，这里可以根据需要扩展。
    # 暂时退回到 OpenAIClient，同时保留一个可读的错误提示。
    # 注意：错误提示会由 Service 层转化为用户可读的信息。
    return OpenAIClient()


