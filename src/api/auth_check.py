# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-27 14:38:49
@LastEditor: Ajax
@LastEditTime: 2026-05-27 14:38:49
@Description: 提供与图片生成流程解耦的 OpenAI 认证独立排查入口。
"""

from dataclasses import dataclass
from pathlib import Path

import openai
from openai import APIConnectionError, AuthenticationError, OpenAI

from src.config.settings import Settings, load_settings, validate_api_key


@dataclass(slots=True)
class AuthCheckResult:
    """独立认证排查结果。"""

    status: str
    message: str
    sdk_version: str
    masked_api_key: str
    model_count: int | None = None


def run_auth_check(settings: Settings) -> AuthCheckResult:
    """用最小独立请求验证当前 API Key 是否被平台接受。"""
    client = OpenAI(api_key=settings.api_key)
    try:
        response = client.models.list()
    except AuthenticationError as exc:
        return AuthCheckResult(
            status="invalid_api_key",
            message=(
                "OpenAI 平台拒绝了当前 OPENAI_API_KEY。"
                " 请确认该 key 来自 https://platform.openai.com/api-keys、"
                "未被撤销、且属于当前可用项目。"
            ),
            sdk_version=openai.__version__,
            masked_api_key=settings.masked_api_key(),
        )
    except APIConnectionError as exc:
        return AuthCheckResult(
            status="network_error",
            message=f"认证检查未连通 OpenAI 平台：{exc}",
            sdk_version=openai.__version__,
            masked_api_key=settings.masked_api_key(),
        )
    except Exception as exc:
        return AuthCheckResult(
            status="unexpected_error",
            message=f"认证检查遇到未预期异常：{type(exc).__name__}: {exc}",
            sdk_version=openai.__version__,
            masked_api_key=settings.masked_api_key(),
        )

    model_count = len(getattr(response, "data", []) or [])
    return AuthCheckResult(
        status="ok",
        message="OpenAI 平台已接受当前 API Key，独立认证检查通过。",
        sdk_version=openai.__version__,
        masked_api_key=settings.masked_api_key(),
        model_count=model_count,
    )


def main() -> int:
    """命令行独立认证检查入口。"""
    project_root = Path(__file__).resolve().parents[2]

    try:
        settings = load_settings(project_root)
        validate_api_key(settings)
    except Exception as exc:
        print(f"认证检查启动失败：{exc}")
        return 1

    result = run_auth_check(settings)
    print(f"status={result.status}")
    print(f"sdk_version={result.sdk_version}")
    print(f"api_key={result.masked_api_key}")
    print(result.message)
    if result.model_count is not None:
        print(f"model_count={result.model_count}")
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
