# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-27 10:13:24
@Description: 负责构造 gpt-image-2 请求，并按运行模式注入受控图片质量参数。
"""

import inspect
from pathlib import Path
from typing import Any

import openai
from openai import OpenAI
from openai.resources.images import Images

from src.config.settings import Settings
from src.config.task_config import TaskConfig


COMMON_QUALITY_VALUES = {"auto", "low", "medium", "high", "standard"}
GENERATE_ONLY_QUALITY_VALUES = {"hd"}


class ImageClientCompatibilityError(RuntimeError):
    """当前 SDK 与 gpt-image-2 请求能力不匹配时抛出。"""


def _validate_sdk_compatibility() -> None:
    """校验当前 SDK 是否具备最小所需调用能力。"""
    required_parameters = {"prompt", "model", "n", "size", "extra_body"}
    generate_signature = inspect.signature(Images.generate)
    generate_parameters = set(generate_signature.parameters.keys())
    missing_generate_parameters = sorted(required_parameters - generate_parameters)
    if missing_generate_parameters:
        raise ImageClientCompatibilityError(
            "当前 OpenAI SDK 与 gpt-image-2 接口能力不匹配，请升级 SDK 或按官方文档调整。"
            f" 缺少参数：{', '.join(missing_generate_parameters)}"
        )

    edit_required_parameters = {"image", "prompt", "model", "n", "output_format"}
    edit_signature = inspect.signature(Images.edit)
    edit_parameters = set(edit_signature.parameters.keys())
    missing_edit_parameters = sorted(edit_required_parameters - edit_parameters)
    if missing_edit_parameters:
        raise ImageClientCompatibilityError(
            "当前 OpenAI SDK 与 gpt-image-2 编辑接口能力不匹配，请升级 SDK 或按官方文档调整。"
            f" 缺少参数：{', '.join(missing_edit_parameters)}"
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
    quality, quality_source = _resolve_request_quality(
        settings=settings,
        request_type=request_type,
    )
    request_payload: dict[str, Any] = {
        "request_type": request_type,
        "body": request_body,
    }
    if quality is not None:
        request_body["quality"] = quality

    if request_type == "generate":
        request_payload["sdk_kwargs"] = {
            "model": settings.model,
            "prompt": final_prompt,
            "n": task_config.image_count,
            "size": task_config.image_size,
            "quality": quality,
            "extra_body": {
                "output_format": output_format,
            },
        }
    else:
        request_payload["sdk_kwargs"] = {
            "model": settings.model,
            "prompt": final_prompt,
            "image": reference_image_paths,
            "n": task_config.image_count,
            "size": task_config.image_size,
            "output_format": output_format,
            "quality": quality,
        }
        if mask_image_path is not None:
            request_payload["sdk_kwargs"]["mask"] = mask_image_path

    if quality is None:
        request_payload["sdk_kwargs"].pop("quality", None)

    request_snapshot = {
        "mode": task_config.mode,
        "model": settings.model,
        "run_mode": settings.run_mode,
        "prompt": final_prompt,
        "size": task_config.image_size,
        "n": task_config.image_count,
        "output_format": output_format,
        "quality": quality,
        "quality_source": quality_source,
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
            response = client.images.edit(**request_payload["sdk_kwargs"])
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


def _resolve_request_quality(settings: Settings, request_type: str) -> tuple[str | None, str]:
    """根据运行模式与显式配置决定本次请求使用的质量参数。"""
    if settings.run_mode == "test":
        forced_quality = "low"
        _validate_quality_value(forced_quality, request_type)
        return forced_quality, "test_forced_low"

    if settings.image_quality is not None:
        _validate_quality_value(settings.image_quality, request_type)
        return settings.image_quality, "explicit"

    default_quality = "high"
    _validate_quality_value(default_quality, request_type)
    return default_quality, "default_high"


def _validate_quality_value(quality: str, request_type: str) -> None:
    """校验质量参数是否适用于当前请求类型。"""
    if quality in COMMON_QUALITY_VALUES:
        return

    if quality in GENERATE_ONLY_QUALITY_VALUES:
        if request_type == "generate":
            return
        raise ValueError("OPENAI_IMAGE_QUALITY=hd 仅支持生成接口，不支持参考图编辑接口。")

    allowed_values = ", ".join(sorted(COMMON_QUALITY_VALUES | GENERATE_ONLY_QUALITY_VALUES))
    raise ValueError(f"不支持的图片质量配置：{quality}。允许值：{allowed_values}")
