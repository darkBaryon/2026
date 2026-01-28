from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseLLMClient(ABC):
    """
    抽象的大模型客户端接口。

    Adapter 层需要实现这个接口，以便在 Service 层通过统一方式调用。
    """

    @abstractmethod
    def generate_reply(self, messages: List[Dict[str, str]]) -> str:
        """
        给定对话消息列表，返回模型回复文本。

        :param messages: OpenAI / DeepSeek 等常见的 messages 格式：
                         [{"role": "system"|"user"|"assistant", "content": "..."}]
        :return: 模型生成的回复文本（已经做过基本清洗）
        """
        raise NotImplementedError

