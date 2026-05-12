# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 15:37:14
@Description: 提供 JSON 文件读取与安全写入能力。
"""

import json
from pathlib import Path
from typing import Any

from src.utils.file_utils import ensure_dir


def read_json_file(path: Path) -> Any:
    """读取 JSON 文件。"""
    if not path.exists():
        raise FileNotFoundError(f"JSON 文件不存在：{path.as_posix()}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败：{path.as_posix()}") from exc


def write_json_file(path: Path, data: Any, *, overwrite: bool = True) -> Path:
    """写入 JSON 文件，默认覆盖当前任务内同名文件。"""
    ensure_dir(path.parent)
    if path.exists() and not overwrite:
        raise FileExistsError(f"JSON 文件已存在，禁止覆盖：{path.as_posix()}")

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
