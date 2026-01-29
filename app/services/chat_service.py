from __future__ import annotations

import logging
from typing import Dict, List

from app.core.llm import BaseLLMClient, get_llm_client
from app.core.prompt_manager import render_prompt
from app.core.search_schema import HouseSearchQuery
from app.services.query_parser import QueryParser

try:
    from data.house_repository import HouseRepository
except ImportError:
    logging.getLogger(__name__).warning(
        "无法导入 data.house_repository，将使用占位实现，查询始终返回空列表。"
    )
    HouseRepository = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        client: BaseLLMClient | None = None,
        repo: HouseRepository | None = None,
    ) -> None:
        self._client: BaseLLMClient = client or get_llm_client()
        # NLU 解析器：负责将对话转为 HouseSearchQuery
        self.parser: QueryParser = QueryParser(self._client)
        self.repo: HouseRepository | None = repo or (HouseRepository() if HouseRepository else None)
        self.history: List[Dict[str, str]] = [
            {
                "role": "assistant",
                "content": "您好，我是【安居找房】深圳区顾问小安。👋 请问您想找哪个区域（比如南山、福田）的房子？预算大概是多少呢？",
            }
        ]

    def _build_chat_messages(
        self,
        user_message: str,
        house_context: str | None = None,
        searched: bool = False,
    ) -> List[Dict[str, str]]:
        """构造发给 LLM 的 messages：system + 历史 + 当前用户输入。"""
        system_prompt = render_prompt(
            "system_chat.j2",
            context=house_context,
            searched=searched,
        )
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history[-10:])
        messages.append({"role": "user", "content": user_message})
        return messages

    def handle_chat(self, user_message: str) -> str:
        text = (user_message or "").strip()
        if not text:
            return "您好，我没有听清楚，可以再说一遍吗？"

        # 入口层之后，再次在 Service 层记录一次用户输入，便于只看某一层日志也能还原上下文
        logger.info("[handle_chat] 收到用户输入: %r", text)

        if text.lower() in ["清空", "reset", "重置"]:
            self.history = [
                {
                    "role": "assistant",
                    "content": "您好，我是【安居找房】深圳区顾问小安。👋 请问您想找哪个区域（比如南山、福田）的房子？预算大概是多少呢？",
                }
            ]
            return "已重置对话。"

        # 1. NLU：参数解析 -> 结构化查询对象
        query: HouseSearchQuery = self.parser.parse(self.history, text)
        logger.info("[handle_chat] NLU 结果: %s", query)

        house_context: str | None = None
        searched = False

        # 2. Query：若需要查库则调用数据层
        if not query.search_intent:
            logger.info("[handle_chat] 未查库: search_intent=False，检索数据=无（AI 不得编造具体房源）")
        elif not self.repo:
            logger.info("[handle_chat] 未查库: repo 不可用，检索数据=无")
        else:
            logger.info(
                "[handle_chat] 开始查库: area=%r, max_price=%s",
                query.area,
                query.max_price,
            )
            houses = self.repo.query_houses(query)
            searched = True
            # 明确记录「检索出的数据」，便于对比 AI 是否编造
            logger.info("[handle_chat] 检索出的数据 共 %d 条:", len(houses))
            for i, h in enumerate(houses):
                logger.info(
                    "[handle_chat]   检索[%d] id=%s area=%s location=%s type=%s price=%s desc=%s",
                    i, h.get("id"), h.get("area"), h.get("location"), h.get("type"), h.get("price"), h.get("desc"),
                )
            if houses:
                house_context = "系统为您检索到以下房源：\n" + "\n".join(
                    f"- [{h['area']}-{h['location']}] {h['type']} {h['price']}元/月，亮点：{h['desc']}"
                    for h in houses
                )
                logger.info("[handle_chat] 注入房源上下文(前300字): %s", (house_context[:300] + "…" if len(house_context) > 300 else house_context))
            else:
                logger.info("[handle_chat] 检索结果: 0 条，searched=True，将走「未找到」话术")

        # 3. NLG：拼 system prompt + 历史 + 当前输入，调用 LLM 生成回复
        messages = self._build_chat_messages(
            text, house_context=house_context, searched=searched
        )
        system_len = len(messages[0]["content"]) if messages else 0
        logger.info("[handle_chat] 发给 LLM: messages 条数=%d, system_prompt 长度=%d, 当前用户输入=%r", len(messages), system_len, text)
        logger.debug("[handle_chat] system_prompt 全文(前500字): %s", messages[0]["content"][:500] + "…" if system_len > 500 else messages[0]["content"])

        try:
            reply = self._client.generate_reply(messages)
            self.history.append({"role": "user", "content": text})
            self.history.append({"role": "assistant", "content": reply})
            logger.info("[handle_chat] AI 回复: 长度=%d, 内容=%r", len(reply), reply)
            return reply
        except Exception as e:
            logger.error(
                "Chat reply generation failed. user_message=%r, error=%s", text, e
            )
            return f"系统繁忙，请稍后再试。（错误：{e}）"
