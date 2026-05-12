# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 15:37:14
@Description: 负责解析响应中的 base64 图片数据并安全保存图片文件。
"""

import base64
from pathlib import Path
from typing import Any

from src.utils.file_utils import write_binary_file


def save_images_from_response(
    response_payload: dict[str, Any],
    images_dir: Path,
    output_format: str,
) -> list[Path]:
    """从响应中提取 b64_json 并保存到 images 目录。"""
    data_items = response_payload.get("data")
    if not isinstance(data_items, list) or not data_items:
        raise ValueError("API 响应中缺少可用的图片数据列表 data。")

    extension = _normalize_extension(output_format)
    saved_paths: list[Path] = []
    for index, item in enumerate(data_items, start=1):
        if not isinstance(item, dict):
            raise ValueError("API 响应中的图片项格式不正确，必须为对象。")

        image_base64 = item.get("b64_json")
        if not image_base64:
            raise ValueError("API 响应中缺少 b64_json，无法保存图片文件。")

        try:
            image_bytes = base64.b64decode(image_base64, validate=True)
        except Exception as exc:
            raise ValueError("API 响应中的 b64_json 不是合法的 base64 图片数据。") from exc

        image_path = images_dir / f"image_{index:03d}.{extension}"
        saved_paths.append(write_binary_file(image_path, image_bytes))

    return saved_paths


def _normalize_extension(output_format: str) -> str:
    """根据输出格式确定图片扩展名。"""
    normalized = output_format.lower()
    if normalized in {"png", "jpeg", "webp"}:
        return normalized
    raise ValueError(f"不支持的图片输出格式：{output_format}")
