from __future__ import annotations

import os
from typing import Any, Dict, List

from openai import OpenAI

from .base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """
    使用 openai>=1.0.0 官方 SDK 调用 Chat Completions 接口。

    - 使用 `OpenAI` 客户端，而不是全局 `openai.ChatCompletion`。
    - 仍然通过环境变量传入密钥，业务参数从 llm_config.json 读取。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        # 1. 敏感信息：从环境变量读取
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY") or ""

        # 2. 业务参数：从配置文件读取
        self.model: str = config.get("model", "gpt-4o-mini")
        self.temperature: float = float(config.get("temperature", 0.5))
        base_url: str | None = config.get("base_url")

        # 3. 初始化官方 SDK 客户端
        client_kwargs: Dict[str, Any] = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            # 新版 SDK 要用 base_url（通常带 /v1）
            client_kwargs["base_url"] = base_url.rstrip("/")

        # 如果既没有 key 也没有 base_url，也可以先创建一个“空”客户端，
        # 在 generate_reply 里会提示还未配置密钥。
        self._client = OpenAI(**client_kwargs) if client_kwargs else None

    def generate_reply(self, messages: List[Dict[str, str]]) -> str:
        """
        使用官方 SDK 的 chat.completions.create 接口生成回复。
        """
        if self._client is None:
            return (
                "（提示：还没有配置 OPENAI_API_KEY / AI_API_KEY，目前是占位回复）\n\n"
                "当你配置好密钥和模型后，这里会返回真实大模型生成的答案。"
            )

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )

            choices = resp.choices or []
            if not choices:
                return "抱歉，AI 接口没有返回内容，请稍后再试。"

            content = choices[0].message.content
            if not content:
                return "抱歉，AI 接口返回内容为空，请稍后再试。"

            return str(content).strip()
        except Exception as e:  # noqa: BLE001
            return f"调用 AI 接口失败：{e}"

