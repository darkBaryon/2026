from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class HouseSearchQuery:
    """
    Schema / 协议层：
    描述从 NLU 解析出来的房源搜索结构化意图。
    """

    # 是否有搜索意图（只要是在找房或问房源，一般就为 True）
    search_intent: bool = False
    # 区域，例如 "南山"、"福田"；None 表示不限 / 暂不确定
    area: Optional[str] = None
    # 预算上限（元/月）；None 表示不限 / 暂不确定
    max_price: Optional[int] = None
    # 未来扩展字段示例：
    # room_type: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "HouseSearchQuery":
        """
        从原始 JSON 字典构造协议对象，做一次温和的类型清洗与兜底。
        """
        if not isinstance(data, dict):
            return cls()

        # search_intent：尽量转为 bool，异常则兜底为 False
        try:
            search_intent = bool(data.get("search_intent", False))
        except Exception:
            search_intent = False

        area = data.get("area")

        # max_price：兼容字符串 / 浮点等，无法解析则置为 None
        raw_max_price = data.get("max_price")
        max_price: Optional[int]
        if raw_max_price is None or raw_max_price == "":
            max_price = None
        else:
            try:
                max_price = int(raw_max_price)
            except (TypeError, ValueError):
                max_price = None

        return cls(
            search_intent=search_intent,
            area=area,
            max_price=max_price,
        )


