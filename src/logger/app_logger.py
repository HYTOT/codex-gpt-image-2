# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 15:50:08
@Description: 提供全局日志、任务日志与敏感信息脱敏能力。
"""

import logging
import re
from pathlib import Path

from src.utils.file_utils import ensure_dir


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def sanitize_text(text: str) -> str:
    """脱敏日志文本中的敏感信息。"""
    sanitized = text
    sanitized = re.sub(
        r"OPENAI_API_KEY\s*=\s*([^\s]+)",
        lambda match: f"OPENAI_API_KEY={_mask_secret(match.group(1))}",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r"Authorization\s*:\s*Bearer\s+([^\s]+)",
        lambda match: f"Authorization: Bearer {_mask_secret(match.group(1))}",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r"sk-[A-Za-z0-9_\-]{8,}(?=[\s'\",]|$)",
        lambda match: _mask_secret(match.group(0)),
        sanitized,
    )
    sanitized = re.sub(
        r"[A-Za-z]:\\[^\"\n]+",
        "[REDACTED_PATH]",
        sanitized,
    )
    return sanitized


def _mask_secret(secret: str) -> str:
    """对密钥进行脱敏。"""
    if len(secret) <= 4:
        return "***"
    return f"{secret[:3]}***{secret[-4:]}"


class SensitiveDataFilter(logging.Filter):
    """统一处理日志消息中的敏感内容。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_text(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                sanitize_text(arg) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


def _reset_handlers(logger: logging.Logger) -> None:
    """避免重复挂载 handler。"""
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def _build_file_handler(log_path: Path) -> logging.Handler:
    """创建文件日志处理器。"""
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(SanitizingFormatter(LOG_FORMAT))
    handler.addFilter(SensitiveDataFilter())
    return handler


def _build_stream_handler() -> logging.Handler:
    """创建控制台日志处理器。"""
    handler = logging.StreamHandler()
    handler.setFormatter(SanitizingFormatter(LOG_FORMAT))
    handler.addFilter(SensitiveDataFilter())
    return handler


class SanitizingFormatter(logging.Formatter):
    """在最终输出前统一脱敏消息与异常堆栈。"""

    def format(self, record: logging.LogRecord) -> str:
        return sanitize_text(super().format(record))


def setup_global_logger(logs_dir: Path) -> logging.Logger:
    """初始化全局日志。"""
    ensure_dir(logs_dir)
    logger = logging.getLogger("codex_gpt_image_2.global")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    _reset_handlers(logger)
    logger.addHandler(_build_file_handler(logs_dir / "app.log"))
    logger.addHandler(_build_stream_handler())
    return logger


def setup_task_logger(task_log_path: Path) -> logging.Logger:
    """初始化任务日志。"""
    ensure_dir(task_log_path.parent)
    logger = logging.getLogger(f"codex_gpt_image_2.task.{task_log_path.parent.parent.name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    _reset_handlers(logger)
    logger.addHandler(_build_file_handler(task_log_path))
    return logger


def log_message(
    global_logger: logging.Logger,
    task_logger: logging.Logger | None,
    level: int,
    message: str,
    *args: object,
) -> None:
    """同时写入全局日志与任务日志。"""
    global_logger.log(level, message, *args)
    if task_logger is not None:
        task_logger.log(level, message, *args)


def log_exception(
    global_logger: logging.Logger,
    task_logger: logging.Logger | None,
    message: str,
    *args: object,
) -> None:
    """同时写入全局日志与任务日志，并附带异常堆栈。"""
    global_logger.exception(message, *args)
    if task_logger is not None:
        task_logger.exception(message, *args)
