"""
数据层：房源查询接口（Repository 模式）。

模拟独立的数据服务，对外只暴露 query_houses(area, max_price)。
数据来源为同目录 house_data 中的 MOCK_HOUSES。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    # 仅用于类型提示，运行时不引入对 app 层的依赖
    from app.core.search_schema import HouseSearchQuery

from data.house_data import MOCK_HOUSES

logger = logging.getLogger(__name__)


class HouseRepository:
    """
    房源仓储：封装房源数据的查询逻辑。

    纯逻辑实现，不依赖 app 包。
    """

    def __init__(self) -> None:
        self._data: List[Dict[str, Any]] = list(MOCK_HOUSES)

    def query_houses(
        self,
        query: "HouseSearchQuery | None" = None,
        *,
        area: str | None = None,
        max_price: int | None = None,
    ) -> List[Dict[str, Any]]:
        """
        按区域和预算上限查询房源。

        :param query: 协议层的 HouseSearchQuery 对象（可选），通常由 NLU 解析得到。
                      如果同时传入 query 和显式的 area / max_price，显式参数优先生效。

        :param area: 意向区域关键词，对房源的 area 或 location 做模糊匹配；None 表示不限制。
        :param max_price: 预算上限（元/月），只保留 price <= max_price；None 表示不限制。
        :return: 按价格升序排序后的前 3 条，每条为房源字典（含 id, area, location, type, price, desc, tags）。
        """
        # 从协议对象中解包检索条件（若提供）
        if query is not None:
            # NLU/Schema 约定：None 表示“不限”，因此仅在当前参数为 None 时才覆盖
            if area is None:
                area = getattr(query, "area", None)
            if max_price is None:
                max_price = getattr(query, "max_price", None)

        logger.info(
            "[Repository] query_houses 输入参数: query=%s, area=%r, max_price=%s",
            query,
            area,
            max_price,
        )

        results = []

        for house in self._data:
            # 区域过滤：area 或 location 包含关键词即命中
            if area and isinstance(area, str) and area.strip():
                area_lower = area.strip()
                h_area = (house.get("area") or "").strip()
                h_location = (house.get("location") or "").strip()
                if area_lower not in h_area and area_lower not in h_location:
                    continue

            # 价格过滤
            if max_price is not None:
                try:
                    price = int(house.get("price", 0))
                    if price > max_price:
                        continue
                except (TypeError, ValueError):
                    continue

            results.append(dict(house))

        # 按价格升序，取前 3 条
        results.sort(key=lambda x: int(x.get("price", 0)))
        top = results[:3]

        logger.info(
            "[Repository] query_houses area=%r max_price=%s -> matched=%d returned=%d",
            area,
            max_price,
            len(results),
            len(top),
        )
        for i, h in enumerate(top):
            logger.info(
                "[Repository] 返回[%d] id=%s area=%s location=%s type=%s price=%s",
                i,
                h.get("id"),
                h.get("area"),
                h.get("location"),
                h.get("type"),
                h.get("price"),
            )
        return top
