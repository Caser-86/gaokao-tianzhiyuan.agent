from typing import ClassVar
from urllib.request import Request

import pytest

from app.services import catalog as catalog_service
from app.services import featured_content, url_safety
from app.services.url_safety import UnsafeExternalUrlError, validate_external_url


@pytest.mark.parametrize(
    "value",
    [
        "https://cdn.example.com/image.png",
        "http://8.8.8.8/resource",
        "https://www.seu.edu.cn/",
    ],
)
def test_validate_external_url_accepts_http_urls(value: str) -> None:
    assert validate_external_url(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "file:///etc/passwd",
        "ftp://cdn.example.com/image.png",
        "https://user:password@cdn.example.com/image.png",
        "https://localhost/image.png",
        "https://metadata.google.internal/computeMetadata/v1/",
        "http://127.0.0.1:8000/health",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/health",
        "https://example.com:bad/image.png",
    ],
)
def test_validate_external_url_rejects_unsafe_urls(value: str) -> None:
    with pytest.raises(UnsafeExternalUrlError):
        validate_external_url(value)


def test_validate_external_url_rejects_empty_and_oversized_values() -> None:
    with pytest.raises(UnsafeExternalUrlError):
        validate_external_url("   ")

    with pytest.raises(UnsafeExternalUrlError):
        validate_external_url("https://example.com/" + ("a" * 2048))


def test_redirect_handler_rejects_unsafe_redirect_target() -> None:
    handler = url_safety._ValidatedRedirectHandler()

    with pytest.raises(UnsafeExternalUrlError):
        handler.redirect_request(
            Request("https://example.com/start"),
            None,
            302,
            "Found",
            {},
            "http://127.0.0.1:8000/admin",
        )


def test_fetch_external_text_rejects_oversized_response(monkeypatch) -> None:
    class FakeResponse:
        headers: ClassVar[dict[str, str]] = {"Content-Length": str(1024 * 1024 + 1)}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def geturl(self) -> str:
            return "https://example.com/"

        def read(self, _limit: int) -> bytes:
            return b"ignored"

    class FakeOpener:
        def open(self, _request, *, timeout: int):
            assert timeout == 8
            return FakeResponse()

    monkeypatch.setattr(url_safety, "build_opener", lambda _handler: FakeOpener())

    with pytest.raises(UnsafeExternalUrlError, match="too large"):
        url_safety.fetch_external_text("https://example.com/")


def test_featured_image_candidate_rejects_unsafe_html_image_url(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "get_school_detail",
        lambda _slug: {"slug": "demo-school", "name": "演示学校"},
    )
    monkeypatch.setattr(
        catalog_service,
        "get_school_website",
        lambda _slug: "https://example.com/",
    )
    monkeypatch.setattr(
        featured_content,
        "fetch_external_text",
        lambda *_args, **_kwargs: (
            '<meta property="og:image" content="http://127.0.0.1:8000/internal.png">',
            "https://example.com/",
        ),
    )

    result = featured_content.fetch_school_image_candidate("demo-school")

    assert result["status"] == "failed"
    assert result["suggested_image_url"] is None
    assert result["message"] == "官网图片地址未通过安全校验"
