from __future__ import annotations

import json
import logging
from typing import Dict, List

from app.core.llm import BaseLLMClient
from app.core.search_schema import HouseSearchQuery

logger = logging.getLogger(__name__)


class QueryParser:
    """
    NLU 组件：
    负责把「对话历史 + 当前输入」解析为结构化的 HouseSearchQuery。
    """

    def __init__(self, client: BaseLLMClient) -> None:
        # 通过依赖注入接收 LLM 客户端，方便单元测试与替换实现
        self._client = client

    def parse(self, history: List[Dict[str, str]], current_input: str) -> HouseSearchQuery:
        """
        将自然语言解析为 HouseSearchQuery。

        :param history: 对话历史（ChatService 维护）
        :param current_input: 当前用户输入
        """
        text = (current_input or "").strip()
        if not text:
            logger.info("[QueryParser] 空输入，返回默认 HouseSearchQuery(search_intent=False)")
            return HouseSearchQuery()

        # 仅取最近若干轮，避免 prompt 过长
        history_text = "\n".join(
            f"{msg.get('role')}: {msg.get('content')}"
            for msg in history[-6:]
        )

        # 明确告知模型目标是填充 HouseSearchQuery Schema
        schema_description = """
你需要根据下面的 Schema 填充一个 JSON 对象（不要多字段）：

HouseSearchQuery = {
  "search_intent": boolean,   // 用户此轮是否在表达找房 / 问房源的意图
  "area": string | null,      // 当前有效的目标区域，例如 "南山"、"福田"；不知道时填 null
  "max_price": integer | null // 预算上限（元/月），无法确定时填 null
}
"""

        prompt = f"""
你是一个【租房需求状态追踪器】。
你的目标是**根据 Schema HouseSearchQuery 输出一个 JSON 对象**，用于驱动后端数据库检索。

请严格按照以下规则工作：

1. 你只负责填充 HouseSearchQuery，不负责生成自然语言回复。
2. 合并对话历史和本轮输入，维护**当前时刻的完整搜索条件**：
   - 继承历史：历史中已经确定的条件（如区域、预算）在用户未修改时必须保留。
   - 增量更新：用户只说“太贵了”“换到福田”表示只更新预算或区域。
   - 重置：用户说“不限区域”“随便看看其他区”时，将 area 设为 null。
3. 只输出一个 JSON，对应 HouseSearchQuery，**不要添加解释文字**。

{schema_description}

📜 对话历史（最多 6 轮）：
{history_text}

👤 用户最新输入：
{text}

现在请**只输出 HouseSearchQuery 对应的 JSON**：
"""

        logger.info(
            "[QueryParser] 构造 NLU Prompt: history_len=%d, prompt_len=%d",
            len(history),
            len(prompt),
        )
        logger.debug(
            "[QueryParser] NLU Prompt 内容(前800字): %s",
            (prompt[:800] + "…") if len(prompt) > 800 else prompt,
        )

        messages = [{"role": "user", "content": prompt}]

        raw_response = ""
        try:
            raw_response = self._client.generate_reply(messages)
            cleaned = raw_response.strip()

            # 兼容 ```json ... ``` 包裹的返回
            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()

            logger.info(
                "[QueryParser] LLM 原始返回: 长度=%d",
                len(cleaned),
            )
            logger.debug(
                "[QueryParser] LLM 原始返回内容: %r",
                cleaned,
            )

            data = json.loads(cleaned)
        except Exception as e:
            logger.error(
                "[QueryParser] 解析 JSON 失败，将回退为 search_intent=False. raw=%r, error=%s",
                raw_response,
                e,
            )
            return HouseSearchQuery()

        query = HouseSearchQuery.from_dict(data)
        logger.info("[QueryParser] 结构化解析结果: %s", query)
        return query


