# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-27 10:54:37
@Description: 负责任务 ID、任务目录与结构化任务 metadata 初始化和更新。
"""

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.utils.file_utils import ensure_dir
from src.utils.json_utils import read_json_file, write_json_file
from src.utils.time_utils import format_datetime, get_beijing_now, get_date_dirname, get_task_timestamp


@dataclass(slots=True)
class TaskContext:
    """任务上下文。"""

    task_id: str
    output_dir: Path
    images_dir: Path
    prompt_dir: Path
    api_dir: Path
    logs_dir: Path
    inputs_dir: Path
    reference_inputs_dir: Path
    mask_inputs_dir: Path
    metadata_path: Path


def create_task_id() -> str:
    """创建唯一任务 ID。"""
    return f"{get_task_timestamp()}_task_{uuid.uuid4().hex[:5]}"


def create_task_directory(task_id: str, project_root: Path, outputs_dir: Path) -> TaskContext:
    """创建任务目录及其固定子目录。"""
    date_dir = project_root / outputs_dir / get_date_dirname()
    ensure_dir(date_dir)

    output_dir = date_dir / task_id
    while output_dir.exists():
        output_dir = date_dir / f"{task_id}_{uuid.uuid4().hex[:4]}"

    images_dir = ensure_dir(output_dir / "images")
    prompt_dir = ensure_dir(output_dir / "prompt")
    api_dir = ensure_dir(output_dir / "api")
    logs_dir = ensure_dir(output_dir / "logs")
    inputs_dir = ensure_dir(output_dir / "inputs")
    reference_inputs_dir = ensure_dir(inputs_dir / "reference")
    mask_inputs_dir = ensure_dir(inputs_dir / "mask")

    return TaskContext(
        task_id=output_dir.name,
        output_dir=output_dir,
        images_dir=images_dir,
        prompt_dir=prompt_dir,
        api_dir=api_dir,
        logs_dir=logs_dir,
        inputs_dir=inputs_dir,
        reference_inputs_dir=reference_inputs_dir,
        mask_inputs_dir=mask_inputs_dir,
        metadata_path=output_dir / "metadata.json",
    )


def init_task_metadata(
    task_context: TaskContext,
    *,
    project_root: Path,
    model: str,
) -> dict[str, Any]:
    """初始化任务 metadata。"""
    now = format_datetime(get_beijing_now())
    metadata = {
        "task_id": task_context.task_id,
        "created_at": now,
        "updated_at": now,
        "model": model,
        "prompt_source_mode": "structured_markdown",
        "source_task_prompt": None,
        "source_raw_task": None,
        "output_dir": task_context.output_dir.relative_to(project_root).as_posix(),
        "image_paths": [],
        "request_path": "api/request.json",
        "response_path": "api/response.json",
        "task_log_path": "logs/task.log",
        "reference_image_paths": [],
        "mask_image_path": None,
        "status": "pending",
        "duration_ms": 0,
        "error": None,
    }
    write_json_file(task_context.metadata_path, metadata)
    return metadata


def update_task_metadata(task_context: TaskContext, updates: dict[str, Any]) -> dict[str, Any]:
    """增量更新任务 metadata。"""
    metadata = read_json_file(task_context.metadata_path)
    metadata.update(updates)
    metadata["updated_at"] = format_datetime(get_beijing_now())
    write_json_file(task_context.metadata_path, metadata)
    return metadata
