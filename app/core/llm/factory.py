# app/core/llm/factory.py
import json
import os
from pathlib import Path
from typing import Dict, Any

from .base import BaseLLMClient
from .openai_client import OpenAIClient

def load_config() -> Dict[str, Any]:
    """
    读取同目录下的 llm_config.json。
    如果文件不存在，则返回空配置。
    """
    config_dir = Path(__file__).parent
    config_path = config_dir / "llm_config.json"

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_llm_client() -> BaseLLMClient:
    """
    简单的 LLM Client 工厂。

    Provider 选择优先级：
    1. 环境变量 AI_PROVIDER
    2. llm_config.json 中的 active_provider
    3. 默认值 "openai"
    """
    full_config = load_config()

    provider_name = os.getenv("AI_PROVIDER") or full_config.get(
        "active_provider", "openai"
    )

    provider_config = full_config.get("providers", {}).get(provider_name, {})

    if provider_name in {"openai", "deepseek"}:
        # DeepSeek 兼容 OpenAI 协议，所以可以复用 OpenAIClient
        return OpenAIClient(config=provider_config)

    # TODO: 在这里扩展其他 Provider，例如：
    # if provider_name == "claude":
    #     return ClaudeClient(config=provider_config)

    # 默认 fallback：回退到 OpenAIClient
    return OpenAIClient(config=provider_config)



