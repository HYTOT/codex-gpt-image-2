# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 15:37:14
@Description: 项目脚本入口，负责启动配置校验与图片生成流程。
"""

from pathlib import Path

from src.config.settings import load_settings, validate_api_key, validate_model
from src.core.generator import run_generation
from src.logger.app_logger import setup_global_logger


def main() -> int:
    """最小脚本入口。"""
    project_root = Path(__file__).resolve().parent

    try:
        settings = load_settings(project_root)
    except Exception as exc:
        print(f"配置加载失败：{exc}")
        return 1

    global_logger = setup_global_logger(project_root / settings.logs_dir)

    try:
        validate_model(settings)
        validate_api_key(settings)
    except Exception as exc:
        global_logger.error("启动校验失败：%s", exc)
        print(f"启动失败：{exc}")
        return 1

    try:
        task_context = run_generation(settings=settings, global_logger=global_logger)
    except Exception as exc:
        global_logger.exception("图片生成流程失败：%s", exc)
        print(f"运行失败：{exc}")
        return 1

    relative_output_dir = task_context.output_dir.relative_to(project_root).as_posix()
    print(f"图片生成完成，输出目录：{relative_output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
