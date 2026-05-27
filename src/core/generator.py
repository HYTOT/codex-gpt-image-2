# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-27 12:14:43
@Description: 编排结构化任务的提示词读取、API 调用与任务落盘流程。
"""

import logging
from pathlib import Path

from src.api.image_client import build_image_request, generate_image
from src.config.settings import Settings
from src.config.task_config import TaskConfig, load_task_config
from src.core.prompt_engine import read_prompt_file, validate_structured_task_prompt
from src.core.task_manager import (
    TaskContext,
    create_task_directory,
    create_task_id,
    init_task_metadata,
    update_task_metadata,
)
from src.logger.app_logger import log_exception, log_message, sanitize_text, setup_task_logger
from src.utils.file_utils import copy_file, write_text_file
from src.utils.image_utils import save_images_from_response
from src.utils.json_utils import write_json_file
from src.utils.time_utils import calculate_duration_ms, get_beijing_now


def run_generation(settings: Settings, global_logger: logging.Logger) -> TaskContext:
    """执行最小图片生成主流程。"""
    task_context = create_task_directory(
        task_id=create_task_id(),
        project_root=settings.project_root,
        outputs_dir=settings.outputs_dir,
    )
    task_logger = setup_task_logger(task_context.logs_dir / "task.log")
    init_task_metadata(
        task_context,
        project_root=settings.project_root,
        model=settings.model,
    )

    relative_output_dir = task_context.output_dir.relative_to(settings.project_root).as_posix()
    start_time = get_beijing_now()
    log_message(
        global_logger,
        task_logger,
        logging.INFO,
        "任务开始：task_id=%s model=%s output_dir=%s",
        task_context.task_id,
        settings.model,
        relative_output_dir,
    )

    try:
        task_config = load_task_config(settings)
        update_task_metadata(
            task_context,
            {
                "source_task_prompt": _to_project_relative_path(task_config.task_prompt_file, settings),
                "source_raw_task": _to_project_relative_path(task_config.raw_task_file, settings),
            },
        )
        log_message(
            global_logger,
            task_logger,
            logging.INFO,
            "任务配置加载完成：task_config=%s prompt_source=%s reference_count=%s",
            _to_project_relative_path(task_config.source_path, settings),
            "structured_markdown",
            len(task_config.reference_images),
        )

        _, final_prompt = _prepare_task_prompt(
            task_context=task_context,
            task_config=task_config,
        )

        reference_snapshot_files, reference_snapshot_rel_paths, mask_snapshot_file, mask_snapshot_rel_path = _snapshot_input_images(
            task_context=task_context,
            task_config=task_config,
        )
        update_task_metadata(
            task_context,
            {
                "reference_image_paths": reference_snapshot_rel_paths,
                "mask_image_path": mask_snapshot_rel_path,
            },
        )

        request_payload, request_snapshot = build_image_request(
            final_prompt,
            settings,
            task_config,
            reference_image_paths=reference_snapshot_files,
            reference_image_rel_paths=reference_snapshot_rel_paths,
            mask_image_path=mask_snapshot_file,
            mask_image_rel_path=mask_snapshot_rel_path,
        )
        request_snapshot["task_config_path"] = _to_project_relative_path(
            task_config.source_path, settings
        )
        request_snapshot["prompt_source_mode"] = "structured_markdown"
        request_snapshot["source_task_prompt"] = _to_project_relative_path(task_config.task_prompt_file, settings)
        request_snapshot["source_raw_task"] = _to_project_relative_path(task_config.raw_task_file, settings)
        write_json_file(task_context.api_dir / "request.json", request_snapshot)
        log_message(
            global_logger,
            task_logger,
            logging.INFO,
            "请求参数摘要：mode=%s model=%s size=%s n=%s output_format=%s quality=%s quality_source=%s reference_count=%s",
            request_snapshot["mode"],
            request_snapshot["model"],
            request_snapshot["size"],
            request_snapshot["n"],
            request_snapshot["output_format"],
            request_snapshot["quality"],
            request_snapshot["quality_source"],
            len(reference_snapshot_rel_paths),
        )

        response_payload = generate_image(settings, request_payload)
        write_json_file(task_context.api_dir / "response.json", response_payload)

        saved_image_paths = save_images_from_response(
            response_payload=response_payload,
            images_dir=task_context.images_dir,
            output_format=task_config.image_format,
        )
        relative_image_paths = [
            path.relative_to(task_context.output_dir).as_posix() for path in saved_image_paths
        ]

        total_duration_ms = calculate_duration_ms(start_time)
        update_task_metadata(
            task_context,
            {
                "image_paths": relative_image_paths,
                "status": "succeeded",
                "duration_ms": total_duration_ms,
                "error": None,
            },
        )
        log_message(
            global_logger,
            task_logger,
            logging.INFO,
            "响应摘要：image_count=%s duration_ms=%s",
            len(relative_image_paths),
            total_duration_ms,
        )
        log_message(
            global_logger,
            task_logger,
            logging.INFO,
            "图片保存完成：%s",
            ", ".join(relative_image_paths),
        )
        return task_context
    except Exception as exc:
        total_duration_ms = calculate_duration_ms(start_time)
        _write_error_response_if_needed(task_context, exc)
        _mark_task_failed(
            task_context=task_context,
            total_duration_ms=total_duration_ms,
            error_message=sanitize_text(f"{type(exc).__name__}: {exc}"),
        )
        log_exception(
            global_logger,
            task_logger,
            "任务失败：task_id=%s error=%s",
            task_context.task_id,
            exc,
        )
        raise


def _mark_task_failed(
    task_context: TaskContext,
    total_duration_ms: int,
    error_message: str,
) -> None:
    """任务失败时更新 metadata。"""
    update_task_metadata(
        task_context,
        {
            "status": "failed",
            "duration_ms": total_duration_ms,
            "error": error_message,
        },
    )


def _write_error_response_if_needed(task_context: TaskContext, exc: Exception) -> None:
    """在 API 已经开始但响应未落盘时，补充错误摘要文件。"""
    request_path = task_context.api_dir / "request.json"
    response_path = task_context.api_dir / "response.json"
    if request_path.exists() and not response_path.exists():
        write_json_file(
            response_path,
            {
                "error": {
                    "type": type(exc).__name__,
                    "message": sanitize_text(str(exc)),
                }
            },
        )


def _snapshot_input_images(
    task_context: TaskContext,
    task_config: TaskConfig,
) -> tuple[list[Path], list[str], Path | None, str | None]:
    """保存参考图与 mask 的任务内快照。"""
    reference_files = []
    reference_paths: list[str] = []
    for index, source_path in enumerate(task_config.reference_images, start=1):
        target_path = task_context.reference_inputs_dir / f"reference_{index:03d}{source_path.suffix.lower()}"
        saved_path = copy_file(source_path, target_path)
        reference_files.append(saved_path)
        reference_paths.append(saved_path.relative_to(task_context.output_dir).as_posix())

    mask_file = None
    mask_path: str | None = None
    if task_config.mask_image is not None:
        target_path = task_context.mask_inputs_dir / f"mask{task_config.mask_image.suffix.lower()}"
        saved_mask_path = copy_file(task_config.mask_image, target_path)
        mask_file = saved_mask_path
        mask_path = saved_mask_path.relative_to(task_context.output_dir).as_posix()
    return reference_files, reference_paths, mask_file, mask_path


def _prepare_task_prompt(
    *,
    task_context: TaskContext,
    task_config: TaskConfig,
) -> tuple[str, str]:
    """准备原始提示词与最终提示词。"""
    raw_prompt = read_prompt_file(task_config.raw_task_file)
    write_text_file(task_context.prompt_dir / "raw_prompt.md", raw_prompt)
    write_json_file(task_context.prompt_dir / "variables.json", {})
    final_prompt = validate_structured_task_prompt(read_prompt_file(task_config.task_prompt_file))
    write_text_file(task_context.prompt_dir / "final_prompt.md", final_prompt)
    return raw_prompt, final_prompt


def _to_project_relative_path(path, settings: Settings) -> str:
    """将项目内路径转换为相对路径字符串。"""
    return path.relative_to(settings.project_root).as_posix()
