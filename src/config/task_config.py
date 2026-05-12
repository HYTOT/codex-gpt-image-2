# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 16:26:00
@LastEditor: Ajax
@LastEditTime: 2026-05-12 17:20:00
@Description: 读取任务配置文件，并解析提示词、变量与参考图输入参数。
"""

from dataclasses import dataclass
from pathlib import Path

from src.config.settings import Settings
from src.utils.json_utils import read_json_file


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(slots=True)
class TaskConfig:
    """当前任务配置。"""

    source_path: Path
    prompt_name: str
    prompt_version: str | None
    variables_file: Path
    reference_images: list[Path]
    mask_image: Path | None
    image_size: str
    image_format: str
    image_count: int

    @property
    def prompt_template_name(self) -> str:
        """模板文件名。"""
        return f"{self.prompt_name}.md"

    @property
    def mode(self) -> str:
        """根据输入判断当前任务模式。"""
        if not self.reference_images:
            return "generate"
        if self.mask_image is not None:
            return "edit_with_mask"
        return "reference_edit"


def load_task_config(settings: Settings) -> TaskConfig:
    """加载任务配置文件。"""
    task_path = settings.project_root / "configs" / "task.json"
    if not task_path.exists():
        task_path = settings.project_root / "configs" / "task.example.json"

    if not task_path.exists():
        raise FileNotFoundError("缺少任务配置文件：configs/task.json 或 configs/task.example.json")

    data = read_json_file(task_path)
    if not isinstance(data, dict):
        raise ValueError(f"任务配置必须是 JSON 对象：{task_path.as_posix()}")

    prompt_name = str(data.get("prompt_name", "default")).strip() or "default"
    prompt_version = str(data.get("prompt_version", "")).strip() or None
    variables_value = str(data.get("variables_file", "")).strip()
    if not variables_value:
        raise ValueError("任务配置缺少 variables_file。")

    reference_images = _resolve_image_list(
        project_root=settings.project_root,
        values=data.get("reference_images", []),
        field_name="reference_images",
    )
    mask_value = str(data.get("mask_image", "") or "").strip()
    mask_image = (
        _resolve_project_file(
            project_root=settings.project_root,
            relative_path=mask_value,
            field_name="mask_image",
            require_image=True,
        )
        if mask_value
        else None
    )

    if mask_image is not None and not reference_images:
        raise ValueError("提供 mask_image 时，reference_images 不能为空。")

    return TaskConfig(
        source_path=task_path,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        variables_file=_resolve_project_file(
            project_root=settings.project_root,
            relative_path=variables_value,
            field_name="variables_file",
            require_image=False,
        ),
        reference_images=reference_images,
        mask_image=mask_image,
        image_size=str(data.get("image_size", settings.default_image_size)).strip()
        or settings.default_image_size,
        image_format=str(data.get("image_format", settings.default_image_format)).strip().lower()
        or settings.default_image_format,
        image_count=int(data.get("image_count", settings.default_image_count)),
    )


def _resolve_image_list(project_root: Path, values: object, field_name: str) -> list[Path]:
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
                relative_path=relative_path,
                field_name=f"{field_name}[{index}]",
                require_image=True,
            )
        )
    return resolved_paths


def _resolve_project_file(
    project_root: Path,
    relative_path: str,
    field_name: str,
    *,
    require_image: bool,
) -> Path:
    """将项目内相对路径解析为真实文件路径，并限制在项目目录内。"""
    candidate_path = (project_root / relative_path).resolve()
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
