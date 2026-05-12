# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 16:26:00
@Description: 负责构造 gpt-image-2 请求并通过 OpenAI SDK 调用图片生成接口。
"""

import inspect
from pathlib import Path
from typing import Any

import openai
from openai import OpenAI
from openai.resources.images import Images
from openai.types.images_response import ImagesResponse

from src.config.settings import Settings
from src.config.task_config import TaskConfig


class ImageClientCompatibilityError(RuntimeError):
    """当前 SDK 与 gpt-image-2 请求能力不匹配时抛出。"""


def _validate_sdk_compatibility() -> None:
    """校验当前 SDK 是否具备最小所需调用能力。"""
    required_parameters = {"prompt", "model", "n", "size", "extra_body"}
    signature = inspect.signature(Images.generate)
    actual_parameters = set(signature.parameters.keys())
    missing_parameters = sorted(required_parameters - actual_parameters)
    if missing_parameters:
        raise ImageClientCompatibilityError(
            "当前 OpenAI SDK 与 gpt-image-2 接口能力不匹配，请升级 SDK 或按官方文档调整。"
            f" 缺少参数：{', '.join(missing_parameters)}"
        )


def build_image_request(
    final_prompt: str,
    settings: Settings,
    task_config: TaskConfig,
    *,
    reference_image_paths: list[Path],
    reference_image_rel_paths: list[str],
    mask_image_path: Path | None,
    mask_image_rel_path: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """构造 gpt-image-2 的请求参数与请求快照。"""
    if settings.model != "gpt-image-2":
        raise ValueError("当前实现只允许使用 gpt-image-2。")

    output_format = task_config.image_format.lower()
    if output_format not in {"png", "jpeg", "webp"}:
        raise ValueError(f"不支持的输出格式：{output_format}")

    request_body = {
        "model": settings.model,
        "prompt": final_prompt,
        "n": task_config.image_count,
        "size": task_config.image_size,
        "output_format": output_format,
    }
    request_type = "generate" if task_config.mode == "generate" else "edit"
    request_payload: dict[str, Any] = {
        "request_type": request_type,
        "body": request_body,
    }

    if request_type == "generate":
        request_payload["sdk_kwargs"] = {
            "model": settings.model,
            "prompt": final_prompt,
            "n": task_config.image_count,
            "size": task_config.image_size,
            "extra_body": {
                "output_format": output_format,
            },
        }
    else:
        request_payload["files"] = _build_edit_files(
            reference_images=reference_image_paths,
            mask_image=mask_image_path,
        )

    request_snapshot = {
        "mode": task_config.mode,
        "model": settings.model,
        "prompt": final_prompt,
        "size": task_config.image_size,
        "n": task_config.image_count,
        "output_format": output_format,
        "reference_images": reference_image_rel_paths,
        "mask_image": mask_image_rel_path,
        "sdk_version": openai.__version__,
    }
    return request_payload, request_snapshot


def generate_image(settings: Settings, request_payload: dict[str, Any]) -> dict[str, Any]:
    """调用 gpt-image-2 生成图片，并返回可落盘的结构化响应。"""
    _validate_sdk_compatibility()

    client = OpenAI(api_key=settings.api_key)
    try:
        if request_payload["request_type"] == "generate":
            response = client.images.generate(**request_payload["sdk_kwargs"])
        else:
            response = client.post(
                "/images/edits",
                cast_to=ImagesResponse,
                body=request_payload["body"],
                files=request_payload["files"],
                options={"headers": {"Content-Type": "multipart/form-data"}},
            )
    except TypeError as exc:
        raise ImageClientCompatibilityError(
            "当前 OpenAI SDK 与 gpt-image-2 接口能力不匹配，请升级 SDK 或按官方文档调整。"
        ) from exc

    if hasattr(response, "model_dump"):
        return response.model_dump()

    # TODO: 如果后续 SDK 返回对象结构变化，这里需要按官方返回结构补充序列化处理。
    return {
        "created": getattr(response, "created", None),
        "data": [
            {
                "b64_json": getattr(item, "b64_json", None),
                "revised_prompt": getattr(item, "revised_prompt", None),
                "url": getattr(item, "url", None),
            }
            for item in getattr(response, "data", [])
        ],
    }


def _build_edit_files(reference_images: list[Path], mask_image: Path | None) -> list[tuple[str, Any]]:
    """构造多参考图编辑请求的 multipart 文件列表。"""
    files: list[tuple[str, Any]] = [("image", image_path) for image_path in reference_images]
    if mask_image is not None:
        files.append(("mask", mask_image))
    return files
