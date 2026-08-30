from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)

DEFAULT_MAX_EXTERNAL_URL_LENGTH = 2048
DEFAULT_MAX_EXTERNAL_RESPONSE_BYTES = 1024 * 1024

_BLOCKED_HOSTNAMES = {
    "host.docker.internal",
    "instance-data.ec2.internal",
    "kubernetes.default.svc",
    "metadata.google.internal",
}
_BLOCKED_LOCAL_SUFFIXES = (
    ".internal",
    ".intranet",
    ".lan",
    ".local",
    ".localhost",
)


class UnsafeExternalUrlError(ValueError):
    """Raised when a URL is not safe to use for an outbound request."""


def _is_unsafe_ip_literal(hostname: str) -> bool:
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False

    return not address.is_global


def validate_external_url(
    value: str,
    *,
    max_length: int = DEFAULT_MAX_EXTERNAL_URL_LENGTH,
) -> str:
    """Validate an outbound HTTP(S) URL without performing a network request.

    Hostnames are deliberately not resolved here. This keeps request validation
    deterministic and avoids turning input validation into an implicit DNS
    dependency. Network-fetching callers additionally validate every redirect.
    """

    if not isinstance(value, str):
        raise UnsafeExternalUrlError("external URL must be a string")

    url = value.strip()
    if not url:
        raise UnsafeExternalUrlError("external URL is required")
    if len(url) > max_length:
        raise UnsafeExternalUrlError("external URL is too long")
    if any(ord(character) < 32 or ord(character) == 127 for character in url):
        raise UnsafeExternalUrlError("external URL contains control characters")

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise UnsafeExternalUrlError("external URL is malformed") from exc

    if parsed.scheme.lower() not in {"http", "https"}:
        raise UnsafeExternalUrlError("only http and https URLs are supported")
    if not hostname:
        raise UnsafeExternalUrlError("external URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeExternalUrlError("external URL must not contain credentials")
    if port is not None and not 1 <= port <= 65535:
        raise UnsafeExternalUrlError("external URL port is invalid")

    normalized_hostname = hostname.rstrip(".").lower()
    if (
        normalized_hostname == "localhost"
        or normalized_hostname in _BLOCKED_HOSTNAMES
        or normalized_hostname.endswith(_BLOCKED_LOCAL_SUFFIXES)
        or normalized_hostname.isdigit()
        or _is_unsafe_ip_literal(normalized_hostname)
    ):
        raise UnsafeExternalUrlError("external URL points to a local or reserved host")

    return url


class _ValidatedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        validate_external_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_external_text(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 8,
    max_bytes: int = DEFAULT_MAX_EXTERNAL_RESPONSE_BYTES,
) -> tuple[str, str]:
    """Fetch a small text page while validating redirects and body size.

    Returns the decoded body and the final validated URL. The caller remains
    responsible for deciding whether the response is the expected media type.
    """

    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")

    safe_url = validate_external_url(url)
    request = Request(safe_url, headers=headers or {})
    opener = build_opener(_ValidatedRedirectHandler())

    with opener.open(request, timeout=timeout) as response:
        final_url = validate_external_url(response.geturl())
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                content_length_value = int(content_length)
            except ValueError as exc:
                raise UnsafeExternalUrlError("external response content length is invalid") from exc
            if content_length_value > max_bytes:
                raise UnsafeExternalUrlError("external response is too large")

        body = response.read(max_bytes + 1)

    if len(body) > max_bytes:
        raise UnsafeExternalUrlError("external response is too large")

    return body.decode("utf-8", errors="ignore"), final_url
