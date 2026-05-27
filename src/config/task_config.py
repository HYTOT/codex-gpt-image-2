# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 16:26:00
@LastEditor: Ajax
@LastEditTime: 2026-05-27 10:54:37
@Description: 读取仅支持六段式结构化任务的配置文件与任务目录资源。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.settings import Settings
from src.utils.json_utils import read_json_file


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_TASK_FIELDS = {
    "reference_images",
    "mask_image",
    "image_size",
    "image_format",
    "image_count",
}


@dataclass(slots=True)
class TaskConfig:
    """当前任务配置。"""

    source_path: Path
    raw_task_file: Path
    task_prompt_file: Path
    reference_images: list[Path]
    mask_image: Path | None
    image_size: str
    image_format: str
    image_count: int

    @property
    def mode(self) -> str:
        """根据输入判断当前任务模式。"""
        if not self.reference_images:
            return "generate"
        if self.mask_image is not None:
            return "edit_with_mask"
        return "reference_edit"


def load_task_config(settings: Settings) -> TaskConfig:
    """加载结构化任务配置文件。"""
    entry_config_path = settings.project_root / "configs" / "task.json"
    if not entry_config_path.exists():
        entry_config_path = settings.project_root / "configs" / "task.example.json"

    if not entry_config_path.exists():
        raise FileNotFoundError("缺少任务配置文件：configs/task.json 或 configs/task.example.json")

    task_path, data, resource_base_dir = _load_task_payload(
        project_root=settings.project_root,
        entry_config_path=entry_config_path,
    )
    _validate_task_schema(data, task_path)

    reference_images = _resolve_image_list(
        project_root=settings.project_root,
        base_dir=resource_base_dir,
        values=data.get("reference_images", []),
        field_name="reference_images",
    )
    mask_value = str(data.get("mask_image", "") or "").strip()
    mask_image = (
        _resolve_project_file(
            project_root=settings.project_root,
            base_dir=resource_base_dir,
            relative_path=mask_value,
            field_name="mask_image",
            require_image=True,
        )
        if mask_value
        else None
    )

    if mask_image is not None and not reference_images:
        raise ValueError("提供 mask_image 时，reference_images 不能为空。")

    image_size = str(data.get("image_size", settings.default_image_size)).strip() or settings.default_image_size
    image_format = str(data.get("image_format", settings.default_image_format)).strip().lower() or settings.default_image_format
    image_count = int(data.get("image_count", settings.default_image_count))

    return TaskConfig(
        source_path=task_path,
        raw_task_file=_resolve_project_file(
            project_root=settings.project_root,
            base_dir=resource_base_dir,
            relative_path="raw_task.md",
            field_name="raw_task.md",
            require_image=False,
        ),
        task_prompt_file=_resolve_project_file(
            project_root=settings.project_root,
            base_dir=resource_base_dir,
            relative_path="task_prompt.md",
            field_name="task_prompt.md",
            require_image=False,
        ),
        reference_images=reference_images,
        mask_image=mask_image,
        image_size=image_size,
        image_format=image_format,
        image_count=image_count,
    )


def _load_task_payload(
    project_root: Path,
    entry_config_path: Path,
) -> tuple[Path, dict[str, Any], Path]:
    """加载任务配置，并根据任务指针确定资源解析基准目录。"""
    data = read_json_file(entry_config_path)
    if not isinstance(data, dict):
        raise ValueError(f"任务配置必须是 JSON 对象：{entry_config_path.as_posix()}")

    task_file_value = str(data.get("task_file", "") or "").strip()
    if not task_file_value:
        raise ValueError("configs/task.json 或 configs/task.example.json 必须包含 task_file。")

    task_path = _resolve_project_file(
        project_root=project_root,
        base_dir=project_root,
        relative_path=task_file_value,
        field_name="task_file",
        require_image=False,
    )
    task_data = read_json_file(task_path)
    if not isinstance(task_data, dict):
        raise ValueError(f"任务配置必须是 JSON 对象：{task_path.as_posix()}")
    return task_path, task_data, task_path.parent


def _resolve_image_list(
    project_root: Path,
    base_dir: Path,
    values: object,
    field_name: str,
) -> list[Path]:
    """解析参考图列表。"""
    if not isinstance(values, list):
        raise ValueError(f"{field_name} 必须是数组。")

    resolved_paths: list[Path] = []
    for index, value in enumerate(values):
        relative_path = str(value).strip()
        if not relative_path:
            raise ValueError(f"{field_name}[{index}] 不能为空字符串。")
        resolved_paths.append(
            _resolve_project_file(
                project_root=project_root,
                base_dir=base_dir,
                relative_path=relative_path,
                field_name=f"{field_name}[{index}]",
                require_image=True,
            )
        )
    return resolved_paths


def _resolve_project_file(
    project_root: Path,
    base_dir: Path,
    relative_path: str,
    field_name: str,
    *,
    require_image: bool,
) -> Path:
    """将基于指定目录的项目内相对路径解析为真实文件路径，并限制在项目目录内。"""
    candidate_path = (base_dir / relative_path).resolve()
    project_root_resolved = project_root.resolve()

    try:
        candidate_path.relative_to(project_root_resolved)
    except ValueError as exc:
        raise ValueError(f"{field_name} 必须位于项目目录内：{relative_path}") from exc

    if not candidate_path.exists() or not candidate_path.is_file():
        raise FileNotFoundError(f"{field_name} 对应文件不存在：{relative_path}")

    if require_image and candidate_path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError(f"{field_name} 必须是图片文件：{relative_path}")
    return candidate_path


def _validate_task_schema(data: dict[str, Any], task_path: Path) -> None:
    """强校验当前任务配置只能使用结构化任务字段。"""
    extra_fields = sorted(set(data.keys()) - ALLOWED_TASK_FIELDS)
    if extra_fields:
        raise ValueError(
            f"结构化任务配置存在已弃用字段：{', '.join(extra_fields)}。"
            f" 请迁移任务目录：{task_path.as_posix()}"
        )
