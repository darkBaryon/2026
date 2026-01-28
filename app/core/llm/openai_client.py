from __future__ import annotations

import os
from typing import Dict, List

import requests

from .base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """
    使用 OpenAI / OpenAI 兼容接口（如部分 DeepSeek 网关）的适配器。

    - 使用环境变量进行配置：
      - AI_API_KEY
      - AI_BASE_URL（默认为 https://api.openai.com/v1/chat/completions）
      - AI_MODEL（如 gpt-4.1-mini / deepseek-chat 等）
      - AI_TIMEOUT（可选，默认 20 秒）
    """

    def __init__(self) -> None:
        self.api_key: str = os.getenv("AI_API_KEY", "")
        self.base_url: str = os.getenv(
            "AI_BASE_URL", "https://api.openai.com/v1/chat/completions"
        )
        self.model: str = os.getenv("AI_MODEL", "gpt-4.1-mini")
        self.timeout: int = int(os.getenv("AI_TIMEOUT", "20"))

    def generate_reply(self, messages: List[Dict[str, str]]) -> str:
        """
        调用兼容 Chat Completions 的 HTTP 接口。

        :param messages: 上下文对话列表，由 Service 层构造
        """
        if not self.api_key:
            # 如果还没配置真实的 API Key，就给出一个友好的提示
            return (
                "（提示：还没有配置真实的 AI_API_KEY，目前是占位回复）\n\n"
                "当你配置好 AI_API_KEY / AI_BASE_URL / AI_MODEL 后，"
                "这里会返回真实大模型生成的答案。"
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
        }

        try:
            resp = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            # OpenAI / 兼容接口常见返回格式：
            # {
            #   "choices": [
            #       {
            #           "message": {"role": "assistant", "content": "..."}
            #       }
            #   ],
            #   ...
            # }
            choices = data.get("choices") or []
            if not choices:
                return "抱歉，AI 接口没有返回内容，请稍后再试。"

            message = choices[0].get("message") or {}
            content = message.get("content")
            if not content:
                return "抱歉，AI 接口返回内容为空，请稍后再试。"

            return str(content).strip()
        except requests.exceptions.RequestException as e:
            # 网络错误、超时、4xx/5xx 等
            return f"调用 AI 接口失败：{e}"
        except Exception as e:  # noqa: BLE001
            return f"解析 AI 返回结果时发生错误：{e}"

