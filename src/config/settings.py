# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 16:26:00
@Description: 读取环境变量与默认配置，并提供模型与密钥校验能力。
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - 仅在本地未安装依赖时走兜底
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        """在缺少 python-dotenv 时保持入口可运行。"""
        return False


@dataclass(slots=True)
class Settings:
    """项目运行配置。"""

    api_key: str
    model: str
    default_image_size: str
    default_image_format: str
    default_image_count: int
    outputs_dir: Path
    logs_dir: Path
    project_root: Path

    def masked_api_key(self) -> str:
        """返回脱敏后的 API Key。"""
        if not self.api_key:
            return ""
        visible_suffix = self.api_key[-4:] if len(self.api_key) >= 4 else self.api_key
        return f"sk-***{visible_suffix}"


def _load_default_config(project_root: Path) -> dict[str, Any]:
    """读取初始化阶段的默认配置文件。"""
    config_path = project_root / "configs" / "config.example.json"
    if not config_path.exists():
        raise FileNotFoundError(f"默认配置文件不存在：{config_path.as_posix()}")

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"默认配置文件解析失败：{config_path.as_posix()}") from exc


def load_settings(project_root: Path) -> Settings:
    """加载 `.env`、环境变量与默认配置。"""
    load_dotenv(project_root / ".env")
    default_config = _load_default_config(project_root)

    model = os.getenv("IMAGE_MODEL", str(default_config["model"])).strip() or "gpt-image-2"
    default_image_size = os.getenv(
        "DEFAULT_IMAGE_SIZE",
        str(default_config["default_image_size"]),
    ).strip()
    default_image_format = os.getenv(
        "DEFAULT_IMAGE_FORMAT",
        str(default_config["default_image_format"]),
    ).strip().lower()
    default_image_count = int(
        os.getenv(
            "DEFAULT_IMAGE_COUNT",
            str(default_config["default_image_count"]),
        ).strip()
    )
    outputs_dir = Path(
        os.getenv("OUTPUTS_DIR", str(default_config["outputs_dir"])).strip() or "outputs"
    )
    logs_dir = Path(
        os.getenv("LOGS_DIR", str(default_config["logs_dir"])).strip() or "logs"
    )

    return Settings(
        api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        model=model,
        default_image_size=default_image_size,
        default_image_format=default_image_format,
        default_image_count=default_image_count,
        outputs_dir=outputs_dir,
        logs_dir=logs_dir,
        project_root=project_root,
    )


def validate_api_key(settings: Settings) -> None:
    """校验是否已配置 API Key。"""
    if not settings.api_key:
        raise ValueError("缺少 OPENAI_API_KEY，请先在 .env 或环境变量中配置后再运行。")


def validate_model(settings: Settings) -> None:
    """强校验模型只能是 gpt-image-2。"""
    if settings.model != "gpt-image-2":
        raise ValueError("IMAGE_MODEL 只允许设置为 gpt-image-2，当前配置不被允许。")
