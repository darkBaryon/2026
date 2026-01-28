from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.core.llm import BaseLLMClient, get_llm_client
from app.core.prompt_manager import render_prompt

try:
    from data.house_repository import HouseRepository
except ImportError:
    logging.getLogger(__name__).warning(
        "无法导入 data.house_repository，将使用占位实现，查询始终返回空列表。"
    )
    HouseRepository = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


# NLU 输出结构：从用户自然语言中提取的查询参数
QueryParams = Dict[str, Any]  # search_intent: bool, area: str | None, max_price: int | None


class ChatService:
    def __init__(
        self,
        client: BaseLLMClient | None = None,
        repo: HouseRepository | None = None,
    ) -> None:
        self._client: BaseLLMClient = client or get_llm_client()
        self.repo: HouseRepository | None = repo or (HouseRepository() if HouseRepository else None)
        self.history: List[Dict[str, str]] = [
            {
                "role": "assistant",
                "content": "您好，我是【安居找房】深圳区顾问小安。👋 请问您想找哪个区域（比如南山、福田）的房子？预算大概是多少呢？",
            }
        ]

    def _extract_query_params(self, user_message: str) -> QueryParams:
        """
        NLU：将用户自然语言转化为结构化查询参数。

        返回 JSON 形如：
        {"search_intent": true, "area": "南山", "max_price": 4000}
        或 {"search_intent": false, "area": null, "max_price": null}
        """
        history_text = "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in self.history[-6:]
        )

        prompt = f"""
你是一个租房场景的意图与参数提取助手。根据「对话历史」和「用户最新回复」，判断用户是否在表达「我要按条件查房源」的意图，并提取查询参数。

对话历史：
{history_text}

用户最新回复：{user_message}

---
请只输出一个标准 JSON 对象，不要其他文字。字段说明：
- search_intent: 用户是否在表达“按区域/预算查房源”的意图（true/false）
- area: 意向区域关键词，如“南山”“福田”“科技园”；若无法提取或无关则 null
- max_price: 预算上限（整数，单位元/月），如“4000以内”-> 4000；若无法提取或无关则 null

示例：
用户说“南山4000以内” -> {{"search_intent": true, "area": "南山", "max_price": 4000}}
用户说“你好” -> {{"search_intent": false, "area": null, "max_price": null}}
"""

        default: QueryParams = {
            "search_intent": False,
            "area": None,
            "max_price": None,
        }

        try:
            messages = [{"role": "user", "content": prompt}]
            response_str = self._client.generate_reply(messages)
            cleaned = response_str.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned)

            search_intent = result.get("search_intent", False)
            area = result.get("area")
            if area is not None and not isinstance(area, str):
                area = str(area).strip() or None
            elif isinstance(area, str):
                area = area.strip() or None

            max_price = result.get("max_price")
            if max_price is not None:
                try:
                    max_price = int(max_price)
                except (TypeError, ValueError):
                    max_price = None

            out: QueryParams = {
                "search_intent": bool(search_intent),
                "area": area,
                "max_price": max_price,
            }
            logger.info("NLU extract_query_params. user_message=%r -> %s", user_message, out)
            return out
        except Exception as e:
            logger.error("NLU extract_query_params failed. user_message=%r, error=%s", user_message, e)
            return default

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

        if text.lower() in ["清空", "reset", "重置"]:
            self.history = [
                {
                    "role": "assistant",
                    "content": "您好，我是【安居找房】深圳区顾问小安。👋 请问您想找哪个区域（比如南山、福田）的房子？预算大概是多少呢？",
                }
            ]
            return "已重置对话。"

        # 1. NLU：参数提取
        params = self._extract_query_params(text)
        logger.info("[handle_chat] NLU 结果: %s", params)

        house_context: str | None = None
        searched = False

        # 2. Query：若需要查库则调用数据层
        if not params.get("search_intent"):
            logger.info("[handle_chat] 未查库: search_intent=False，检索数据=无（AI 不得编造具体房源）")
        elif not self.repo:
            logger.info("[handle_chat] 未查库: repo 不可用，检索数据=无")
        else:
            area = params.get("area")
            max_price = params.get("max_price")
            logger.info("[handle_chat] 开始查库: area=%r, max_price=%s", area, max_price)
            houses = self.repo.query_houses(area=area, max_price=max_price)
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
