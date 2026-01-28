from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)


def _get_prompts_dir() -> Path:
    """获取 prompts 目录路径"""
    # 从 app/core/prompt_manager.py 定位到 app/prompts/
    current_file = Path(__file__)
    prompts_dir = current_file.parent.parent / "prompts"
    return prompts_dir


def render_prompt(template_name: str, **kwargs: str | bool | None) -> str:
    """
    渲染 Jinja2 模板，支持热更新（每次调用都重新读取文件）。

    :param template_name: 模板文件名（如 "system_chat.j2"）
    :param kwargs: 传递给模板的变量（如 context="...", searched=True）
    :return: 渲染后的提示词文本
    :raises TemplateNotFound: 如果模板文件不存在
    """
    prompts_dir = _get_prompts_dir()

    if not prompts_dir.exists():
        logger.error("Prompts directory not found: %s", prompts_dir)
        raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")

    # 每次调用都创建新的 Environment，确保热更新
    env = Environment(
        loader=FileSystemLoader(str(prompts_dir)),
        autoescape=False,  # 提示词不需要 HTML 转义
    )

    try:
        template = env.get_template(template_name)
        rendered = template.render(**kwargs)
        logger.debug(
            "Prompt rendered. template=%s, kwargs_keys=%s",
            template_name,
            list(kwargs.keys()),
        )
        return rendered.strip()
    except TemplateNotFound as e:
        logger.error("Template not found: %s in directory %s", template_name, prompts_dir)
        raise
    except Exception as e:
        logger.error(
            "Failed to render template %s with kwargs %s: %s",
            template_name,
            kwargs,
            e,
        )
        raise
