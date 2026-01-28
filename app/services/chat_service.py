from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.core.llm import BaseLLMClient, get_llm_client
from app.core.prompt_manager import render_prompt

# 🔥 核心修改：从根目录的 data 包导入 house_data
try:
    from data.house_data import search_houses
except ImportError:
    # 兼容性处理：如果运行方式不同，可能需要调整路径，或者提示用户
    logging.getLogger(__name__).warning(
        "无法导入 data.house_data，请检查目录结构。搜索房源会退化为返回空列表。"
    )

    def search_houses(keywords: List[str]) -> List[Dict[str, Any]]:  # type: ignore[misc]
        return []


logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, client: BaseLLMClient | None = None) -> None:
        self._client: BaseLLMClient = client or get_llm_client()
        # 初始化租房顾问欢迎语 (深圳版)
        self.history: List[Dict[str, str]] = [
            {
                "role": "assistant", 
                "content": "您好，我是【安居找房】深圳区顾问小安。👋 请问您想找哪个区域（比如南山、福田）的房子？预算大概是多少呢？"
            }
        ]


    def _analyze_intent(self, user_message: str) -> Dict[str, Any]:
        """意图识别（逻辑保持不变）"""
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history[-6:]])
        
        prompt = f"""
你是一个意图识别助手。请分析下面的对话历史和用户最新回复。
判断用户是否**已经明确提供了**以下两个关键租房需求：
1. **意向区域** (如：南山、福田、宝安、科技园等)
2. **预算范围** (如：5000左右、6000以内等)

对话历史：
{history_text}
用户最新回复：{user_message}

---
请**只输出一个标准的 JSON 对象**。
格式如下：
{{
    "should_search": true/false,
    "keywords": ["关键词1", "关键词2"] 
}}
"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response_str = self._client.generate_reply(messages)
            cleaned_str = response_str.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_str)
            logger.info("Intent analysis success. user_message=%r, result=%s", user_message, result)
            return result
        except Exception as e:
            logger.error("Intent analysis failed. user_message=%r, error=%s", user_message, e)
            return {"should_search": False, "keywords": []}

    def _build_chat_messages(
        self, user_message: str, house_context: str | None = None, searched: bool = False
    ) -> List[Dict[str, str]]:
        """
        构造最终回复用户的 messages。

        :param user_message: 用户输入
        :param house_context: 房源搜索结果文本（如果有）
        :param searched: 是否执行了搜索（用于模板判断）
        """
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
                {"role": "assistant", "content": "您好，我是【安居找房】深圳区顾问小安。👋 请问您想找哪个区域的房子？预算大概是多少呢？"}
            ]
            return "已重置对话。"

        # 1. 思考
        analysis = self._analyze_intent(text)
        logger.debug("Intent analysis raw result: %s", analysis)

        house_context: str | None = None
        searched = False

        # 2. 行动
        if analysis.get("should_search"):
            keywords = analysis.get("keywords", [])
            houses = search_houses(keywords)
            searched = True

            if houses:
                # 格式化房源信息，传递给模板
                house_context = "系统为您检索到以下房源：\n" + "\n".join([
                    f"- [{h['area']}-{h['location']}] {h['type']} {h['price']}元/月，亮点：{h['desc']}"
                    for h in houses
                ])
                logger.info(
                    "House search hit. keywords=%s, count=%d",
                    keywords,
                    len(houses),
                )
            else:
                logger.info("House search no result. keywords=%s", keywords)

        # 3. 回复
        messages = self._build_chat_messages(text, house_context=house_context, searched=searched)

        try:
            reply = self._client.generate_reply(messages)
            self.history.append({"role": "user", "content": text})
            self.history.append({"role": "assistant", "content": reply})
            # 只记录前 80 个字符，避免日志过长
            logger.debug(
                "Chat reply generated. user_message=%r, reply_preview=%r",
                text,
                (reply[:80] + "…") if len(reply) > 80 else reply,
            )
            return reply
        except Exception as e:
            logger.error("Chat reply generation failed. user_message=%r, error=%s", text, e)
            return f"系统繁忙，请稍后再试。（错误：{e}）"