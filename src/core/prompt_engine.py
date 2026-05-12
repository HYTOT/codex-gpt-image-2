# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 15:37:14
@Description: 负责提示词文件读取、变量读取、版本索引与模板渲染。
"""

import re
from pathlib import Path
from typing import Any

from src.utils.json_utils import read_json_file


VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


class PromptVariableError(ValueError):
    """模板变量缺失异常。"""


def read_prompt_file(path: Path) -> str:
    """读取 Markdown 提示词文件。"""
    if not path.exists():
        raise FileNotFoundError(f"提示词文件不存在：{path.as_posix()}")
    return path.read_text(encoding="utf-8")


def read_variables_file(path: Path) -> dict[str, Any]:
    """读取变量 JSON 文件。"""
    data = read_json_file(path)
    if not isinstance(data, dict):
        raise ValueError(f"变量文件内容必须为 JSON 对象：{path.as_posix()}")
    return data


def render_prompt_template(template: str, variables: dict[str, Any]) -> str:
    """执行双花括号变量替换。"""
    required_variables = set(VARIABLE_PATTERN.findall(template))
    missing_variables = sorted(name for name in required_variables if name not in variables)
    if missing_variables:
        raise PromptVariableError(
            f"提示词模板存在缺失变量：{', '.join(missing_variables)}"
        )

    def _replace(match: re.Match[str]) -> str:
        variable_name = match.group(1)
        return str(variables[variable_name])

    return VARIABLE_PATTERN.sub(_replace, template)


def get_latest_prompt_version(index_path: Path, prompt_name: str) -> str:
    """从版本索引中获取最新提示词版本文件名。"""
    index_data = read_json_file(index_path)
    if prompt_name not in index_data:
        raise KeyError(f"提示词索引中不存在名称：{prompt_name}")

    prompt_entry = index_data[prompt_name]
    latest = prompt_entry.get("latest")
    if not latest:
        raise ValueError(f"提示词索引缺少 latest 配置：{prompt_name}")
    return str(latest)
