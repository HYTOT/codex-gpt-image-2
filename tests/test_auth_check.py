# -*- coding: utf-8 -*-
"""
@Author: Ajax
@Date: 2026-05-27 14:38:49
@LastEditor: Ajax
@LastEditTime: 2026-05-27 14:38:49
@Description: 覆盖 OpenAI 独立认证检查与图片接口认证异常提示测试。
"""

from pathlib import Path

import pytest

from src.api import auth_check as auth_check_module
from src.api import image_client as image_client_module
from src.config.settings import Settings


class FakeAuthError(Exception):
    """用于测试的认证异常。"""


class FakeResponse:
    """用于测试的最小响应对象。"""

    def __init__(self, data: list[object]) -> None:
        self.data = data


def _build_settings() -> Settings:
    return Settings(
        api_key="sk-test-valid",
        model="gpt-image-2",
        run_mode="production",
        image_quality=None,
        default_image_size="1024x1024",
        default_image_format="png",
        default_image_count=1,
        outputs_dir=Path("outputs"),
        logs_dir=Path("logs"),
        project_root=Path("E:/codes/codex-gpt-image-2"),
    )


def test_run_auth_check_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.models = self

        def list(self) -> FakeResponse:
            return FakeResponse([object(), object()])

    monkeypatch.setattr(auth_check_module, "OpenAI", FakeClient)

    result = auth_check_module.run_auth_check(_build_settings())

    assert result.status == "ok"
    assert result.model_count == 2
    assert "独立认证检查通过" in result.message


def test_run_auth_check_invalid_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.models = self

        def list(self) -> FakeResponse:
            raise FakeAuthError("bad key")

    monkeypatch.setattr(auth_check_module, "OpenAI", FakeClient)
    monkeypatch.setattr(auth_check_module, "AuthenticationError", FakeAuthError)

    result = auth_check_module.run_auth_check(_build_settings())

    assert result.status == "invalid_api_key"
    assert "platform.openai.com/api-keys" in result.message


def test_generate_image_wraps_invalid_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeImages:
        def edit(self, **kwargs: object) -> FakeResponse:
            raise FakeAuthError("bad key")

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            self.images = FakeImages()

    monkeypatch.setattr(image_client_module, "_validate_sdk_compatibility", lambda: None)
    monkeypatch.setattr(image_client_module, "OpenAI", FakeClient)
    monkeypatch.setattr(image_client_module, "AuthenticationError", FakeAuthError)

    with pytest.raises(image_client_module.ImageClientAuthenticationError, match="src.api.auth_check"):
        image_client_module.generate_image(
            _build_settings(),
            {
                "request_type": "edit",
                "sdk_kwargs": {
                    "model": "gpt-image-2",
                    "prompt": "test",
                    "image": [],
                    "n": 1,
                    "size": "1024x1024",
                    "output_format": "png",
                },
            },
        )
