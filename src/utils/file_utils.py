# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 16:26:00
@Description: 提供安全目录创建与非覆盖文件写入能力。
"""

import shutil
from pathlib import Path


def ensure_dir(directory: Path) -> Path:
    """确保目录存在。"""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_non_conflicting_path(path: Path) -> Path:
    """在目标文件已存在时自动追加数字后缀，避免覆盖历史文件。"""
    if not path.exists():
        return path

    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{index:03d}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def write_text_file(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    overwrite: bool = False,
) -> Path:
    """安全写入文本文件。"""
    ensure_dir(path.parent)
    target_path = path if overwrite else get_non_conflicting_path(path)
    target_path.write_text(content, encoding=encoding)
    return target_path


def write_binary_file(path: Path, content: bytes, *, overwrite: bool = False) -> Path:
    """安全写入二进制文件。"""
    ensure_dir(path.parent)
    target_path = path if overwrite else get_non_conflicting_path(path)
    target_path.write_bytes(content)
    return target_path


def copy_file(source_path: Path, target_path: Path, *, overwrite: bool = False) -> Path:
    """复制文件并避免覆盖历史文件。"""
    ensure_dir(target_path.parent)
    destination_path = target_path if overwrite else get_non_conflicting_path(target_path)
    shutil.copy2(source_path, destination_path)
    return destination_path
