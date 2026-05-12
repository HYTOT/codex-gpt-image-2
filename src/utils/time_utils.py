# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-12 15:37:14
@LastEditor: Ajax
@LastEditTime: 2026-05-12 15:37:14
@Description: 提供北京时间、任务时间戳与耗时计算能力。
"""

from datetime import datetime, timedelta, timezone


BEIJING_TIMEZONE = timezone(timedelta(hours=8))


def get_beijing_now() -> datetime:
    """获取当前北京时间。"""
    return datetime.now(BEIJING_TIMEZONE)


def format_datetime(value: datetime) -> str:
    """格式化时间字符串。"""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def get_date_dirname() -> str:
    """生成日期目录名。"""
    return get_beijing_now().strftime("%Y-%m-%d")


def get_task_timestamp() -> str:
    """生成任务时间戳。"""
    return get_beijing_now().strftime("%Y%m%d_%H%M%S")


def calculate_duration_ms(start_time: datetime, end_time: datetime | None = None) -> int:
    """计算毫秒级耗时。"""
    finished_at = end_time or get_beijing_now()
    duration = finished_at - start_time
    return int(duration.total_seconds() * 1000)
