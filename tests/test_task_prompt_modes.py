# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-27 10:54:37
@LastEditor: Ajax
@LastEditTime: 2026-05-27 15:27:27
@Description: 覆盖仅结构化任务模式下的配置加载、最小提示词检查与请求快照测试。
"""

import json
import logging
from pathlib import Path

import pytest

from src.config.settings import Settings
from src.config.task_config import load_task_config
from src.core import generator as generator_module
from src.core.prompt_engine import StructuredPromptValidationError, validate_structured_task_prompt
from src.utils.json_utils import read_json_file


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_settings(
    project_root: Path,
    *,
    run_mode: str = "production",
    image_quality: str | None = None,
) -> Settings:
    return Settings(
        api_key="sk-test",
        model="gpt-image-2",
        run_mode=run_mode,
        image_quality=image_quality,
        default_image_size="1024x1024",
        default_image_format="png",
        default_image_count=1,
        outputs_dir=Path("outputs"),
        logs_dir=Path("logs"),
        project_root=project_root,
    )


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("codex_gpt_image_2.tests")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.NullHandler())
    return logger


def _build_valid_structured_prompt() -> str:
    return (
        "## 场景\n"
        "- 室内桌面场景，光线干净稳定。\n\n"
        "## 主体\n"
        "- 主体是一只浅色陶瓷杯，造型简洁。\n\n"
        "## 关键细节\n"
        "- 杯口有轻微热气，杯身有细腻高光。\n"
        "- 桌面保留少量自然阴影，避免空漂。\n\n"
        "## 用途\n"
        "- 用于商品质感概念图，便于快速看构图方向。\n\n"
        "## 约束\n"
        "- 避免额外文字和复杂背景。\n\n"
        "## 特别要求\n"
        "- 视为全新独立任务，只描述当前目标。\n"
    )


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    _write_json(
        tmp_path / "configs" / "config.example.json",
        {
            "model": "gpt-image-2",
            "default_image_size": "1024x1024",
            "default_image_format": "png",
            "default_image_count": 1,
            "outputs_dir": "outputs",
            "logs_dir": "logs",
        },
    )
    return tmp_path


def test_load_task_config_structured_mode(project_root: Path) -> None:
    _write_json(project_root / "configs" / "task.json", {"task_file": "tasks/structured/task.json"})
    _write_json(
        project_root / "tasks" / "structured" / "task.json",
        {
            "reference_images": [],
            "mask_image": "",
            "image_size": "1536x1024",
            "image_format": "png",
            "image_count": 1,
        },
    )
    _write_text(project_root / "tasks" / "structured" / "raw_task.md", "原始需求")
    _write_text(project_root / "tasks" / "structured" / "task_prompt.md", _build_valid_structured_prompt())

    task_config = load_task_config(_build_settings(project_root))

    assert task_config.raw_task_file == project_root / "tasks" / "structured" / "raw_task.md"
    assert task_config.task_prompt_file == project_root / "tasks" / "structured" / "task_prompt.md"
    assert task_config.mode == "generate"


def test_load_task_config_rejects_deprecated_fields(project_root: Path) -> None:
    _write_json(project_root / "configs" / "task.json", {"task_file": "tasks/bad/task.json"})
    _write_json(
        project_root / "tasks" / "bad" / "task.json",
        {
            "prompt_name": "default",
            "reference_images": [],
            "mask_image": "",
            "image_size": "1024x1024",
            "image_format": "png",
            "image_count": 1,
        },
    )
    _write_text(project_root / "tasks" / "bad" / "raw_task.md", "原始需求")
    _write_text(project_root / "tasks" / "bad" / "task_prompt.md", _build_valid_structured_prompt())

    with pytest.raises(ValueError, match="已弃用字段"):
        load_task_config(_build_settings(project_root))


def test_load_task_config_requires_task_prompt_file(project_root: Path) -> None:
    _write_json(project_root / "configs" / "task.json", {"task_file": "tasks/missing_prompt/task.json"})
    _write_json(
        project_root / "tasks" / "missing_prompt" / "task.json",
        {
            "reference_images": [],
            "mask_image": "",
            "image_size": "1024x1024",
            "image_format": "png",
            "image_count": 1,
        },
    )
    _write_text(project_root / "tasks" / "missing_prompt" / "raw_task.md", "原始需求")

    with pytest.raises(FileNotFoundError, match="task_prompt.md 对应文件不存在"):
        load_task_config(_build_settings(project_root))


def test_validate_structured_task_prompt_success() -> None:
    final_prompt = validate_structured_task_prompt(_build_valid_structured_prompt())

    assert final_prompt.startswith("## 场景\n- ")
    assert "## 特别要求\n- 视为全新独立任务，只描述当前目标。\n" in final_prompt


def test_validate_structured_task_prompt_accepts_non_structured_text() -> None:
    final_prompt = validate_structured_task_prompt("保留一段自由格式提示词。\r\n第二行继续说明。")

    assert final_prompt == "保留一段自由格式提示词。\n第二行继续说明。\n"


def test_validate_structured_task_prompt_rejects_empty_text() -> None:
    with pytest.raises(StructuredPromptValidationError, match="task_prompt.md 不能为空"):
        validate_structured_task_prompt(" \n\r\n ")


def test_run_generation_structured_mode_writes_request_snapshot(
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_json(project_root / "configs" / "task.json", {"task_file": "tasks/structured_run/task.json"})
    _write_json(
        project_root / "tasks" / "structured_run" / "task.json",
        {
            "reference_images": [],
            "mask_image": "",
            "image_size": "1024x1024",
            "image_format": "png",
            "image_count": 1,
        },
    )
    _write_text(project_root / "tasks" / "structured_run" / "raw_task.md", "这是一段原始需求归档。")
    _write_text(project_root / "tasks" / "structured_run" / "task_prompt.md", _build_valid_structured_prompt())

    def fake_generate_image(_settings: Settings, _request_payload: dict[str, object]) -> dict[str, object]:
        return {"data": [{"b64_json": "ignored"}]}

    def fake_save_images_from_response(
        *,
        response_payload: dict[str, object],
        images_dir: Path,
        output_format: str,
    ) -> list[Path]:
        image_path = images_dir / f"image_001.{output_format}"
        image_path.write_bytes(b"image")
        return [image_path]

    monkeypatch.setattr(generator_module, "generate_image", fake_generate_image)
    monkeypatch.setattr(generator_module, "save_images_from_response", fake_save_images_from_response)

    task_context = generator_module.run_generation(
        settings=_build_settings(project_root, run_mode="test", image_quality="high"),
        global_logger=_build_logger(),
    )
    request_snapshot = read_json_file(task_context.api_dir / "request.json")
    metadata = read_json_file(task_context.metadata_path)

    assert request_snapshot["prompt_source_mode"] == "structured_markdown"
    assert request_snapshot["quality"] == "low"
    assert request_snapshot["quality_source"] == "test_forced_low"
    assert metadata["prompt_source_mode"] == "structured_markdown"
    assert metadata["source_task_prompt"] == "tasks/structured_run/task_prompt.md"
    assert metadata["source_raw_task"] == "tasks/structured_run/raw_task.md"
    assert sorted(path.name for path in task_context.prompt_dir.iterdir()) == [
        "final_prompt.md",
        "raw_prompt.md",
    ]


def test_run_generation_structured_mode_failure_updates_metadata(
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_json(project_root / "configs" / "task.json", {"task_file": "tasks/structured_bad/task.json"})
    _write_json(
        project_root / "tasks" / "structured_bad" / "task.json",
        {
            "reference_images": [],
            "mask_image": "",
            "image_size": "1024x1024",
            "image_format": "png",
            "image_count": 1,
        },
    )
    _write_text(project_root / "tasks" / "structured_bad" / "raw_task.md", "失败任务原始需求。")
    _write_text(
        project_root / "tasks" / "structured_bad" / "task_prompt.md",
        " \n",
    )

    def fail_if_called(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("任务提示词为空时不应继续调用图片接口。")

    monkeypatch.setattr(generator_module, "generate_image", fail_if_called)

    with pytest.raises(StructuredPromptValidationError):
        generator_module.run_generation(
            settings=_build_settings(project_root),
            global_logger=_build_logger(),
        )

    task_dirs = list((project_root / "outputs").rglob("metadata.json"))
    assert len(task_dirs) == 1
    metadata = read_json_file(task_dirs[0])
    assert metadata["status"] == "failed"
    assert "task_prompt.md 不能为空" in metadata["error"]
    assert (task_dirs[0].parent / "prompt" / "raw_prompt.md").read_text(encoding="utf-8") == "失败任务原始需求。\n"


def test_run_generation_allows_non_structured_task_prompt(
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_json(project_root / "configs" / "task.json", {"task_file": "tasks/freeform/task.json"})
    _write_json(
        project_root / "tasks" / "freeform" / "task.json",
        {
            "reference_images": [],
            "mask_image": "",
            "image_size": "1024x1024",
            "image_format": "png",
            "image_count": 1,
        },
    )
    _write_text(project_root / "tasks" / "freeform" / "raw_task.md", "自由格式原始需求。")
    _write_text(
        project_root / "tasks" / "freeform" / "task_prompt.md",
        "一句自由格式提示词，不按六段式编排，但内容非空。",
    )

    def fake_generate_image(_settings: Settings, _request_payload: dict[str, object]) -> dict[str, object]:
        return {"data": [{"b64_json": "ignored"}]}

    def fake_save_images_from_response(
        *,
        response_payload: dict[str, object],
        images_dir: Path,
        output_format: str,
    ) -> list[Path]:
        image_path = images_dir / f"image_001.{output_format}"
        image_path.write_bytes(b"image")
        return [image_path]

    monkeypatch.setattr(generator_module, "generate_image", fake_generate_image)
    monkeypatch.setattr(generator_module, "save_images_from_response", fake_save_images_from_response)

    task_context = generator_module.run_generation(
        settings=_build_settings(project_root),
        global_logger=_build_logger(),
    )

    assert (task_context.prompt_dir / "final_prompt.md").read_text(encoding="utf-8") == (
        "一句自由格式提示词，不按六段式编排，但内容非空。\n"
    )


def test_run_generation_rejects_empty_raw_task(
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_json(project_root / "configs" / "task.json", {"task_file": "tasks/empty_raw/task.json"})
    _write_json(
        project_root / "tasks" / "empty_raw" / "task.json",
        {
            "reference_images": [],
            "mask_image": "",
            "image_size": "1024x1024",
            "image_format": "png",
            "image_count": 1,
        },
    )
    _write_text(project_root / "tasks" / "empty_raw" / "raw_task.md", "\n \r\n")
    _write_text(project_root / "tasks" / "empty_raw" / "task_prompt.md", "非空提示词。")

    def fail_if_called(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("原始需求为空时不应继续调用图片接口。")

    monkeypatch.setattr(generator_module, "generate_image", fail_if_called)

    with pytest.raises(StructuredPromptValidationError, match="raw_task.md 不能为空"):
        generator_module.run_generation(
            settings=_build_settings(project_root),
            global_logger=_build_logger(),
        )
