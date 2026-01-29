from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class ColorFormatter(logging.Formatter):
    """
    彩色控制台日志格式化器。

    仅用于 stdout，不影响文件日志。
    """

    # ANSI 颜色码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[1;41m",  # 粗体红底
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        # [时间] [LEVEL] [模块:行号] - 消息
        base_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
        formatter = logging.Formatter(base_format, datefmt="%Y-%m-%d %H:%M:%S")
        msg = formatter.format(record)
        if color:
            # 只为 [LEVEL] 部分加颜色
            colored = msg.replace(
                f"[{levelname}]",
                f"{color}[{levelname}]{self.RESET}",
                1,
            )
            return colored
        return msg


def _ensure_log_dir(base_dir: str | os.PathLike[str]) -> Path:
    log_dir = Path(base_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def configure_logging(app: Any) -> None:
    """
    全局日志配置：
    - 彩色控制台输出
    - 轮转文件日志 logs/app.log
    """
    # 避免重复配置（例如 Flask 热重载）
    root_logger = logging.getLogger()
    if getattr(root_logger, "_ai_demo_configured", False):
        return

    # 控制台我们希望能看到尽可能完整的调用链路，因此根 logger 设为 DEBUG，
    # 具体输出粒度由各 Handler 自己控制（文件仍然从 INFO 开始记录）。
    root_logger.setLevel(logging.DEBUG)

    # 目录：以项目根目录为基准
    base_dir = getattr(app, "root_path", os.getcwd())
    log_dir = _ensure_log_dir(base_dir)

    # 控制台 Handler（带颜色）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColorFormatter())

    # 文件 Handler（纯文本 + 轮转）
    file_path = log_dir / "app.log"
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 第三方库降噪：只保留 WARNING 及以上，避免刷屏底层 HTTP 细节
    noisy_libs = ["werkzeug", "httpx", "httpcore", "openai", "urllib3"]
    for name in noisy_libs:
        logging.getLogger(name).setLevel(logging.WARNING)

    # 标记避免重复初始化
    root_logger._ai_demo_configured = True  # type: ignore[attr-defined]

    # 给应用本身打一条启动日志
    logger = logging.getLogger("app")
    logger.info("Logging configured. Log file: %s", file_path)


