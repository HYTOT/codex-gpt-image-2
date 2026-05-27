# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-27 12:14:43
@Description: 负责结构化任务提示词文件读取、最小非空检查与换行标准化。
"""

from pathlib import Path


class StructuredPromptValidationError(ValueError):
    """结构化任务提示词最小校验异常。"""


def read_prompt_file(path: Path) -> str:
    """读取 Markdown 提示词文件，并执行最小非空检查。"""
    if not path.exists():
        raise FileNotFoundError(f"提示词文件不存在：{path.as_posix()}")
    return _normalize_prompt_text(path.read_text(encoding="utf-8"), path.name)


def validate_structured_task_prompt(prompt_text: str) -> str:
    """标准化任务提示词文本，不再在运行时执行六段式结构过滤。"""
    return _normalize_prompt_text(prompt_text, "task_prompt.md")


def _normalize_prompt_text(prompt_text: str, prompt_name: str) -> str:
    """标准化换行并确保提示词文件非空。"""
    normalized_text = prompt_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized_text:
        raise StructuredPromptValidationError(f"{prompt_name} 不能为空。")
    return normalized_text + "\n"
