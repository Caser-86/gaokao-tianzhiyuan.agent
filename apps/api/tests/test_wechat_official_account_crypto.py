from __future__ import annotations

import base64
import subprocess
import sys
from hashlib import sha1
from pathlib import Path

import pytest

from app.services.wechat_official_account_crypto import (
    WeChatOfficialAccountCryptoError,
    build_wechat_msg_signature,
    decrypt_wechat_message,
    encrypt_wechat_message,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = REPO_ROOT / "scripts" / "wechat_aes_helper.py"
RAW_AES_KEY = b"0123456789abcdef0123456789abcdef"
ENCODING_AES_KEY = base64.b64encode(RAW_AES_KEY).decode("utf-8")[:-1]
APP_ID = "wx-test-appid"


def test_build_wechat_msg_signature_sorts_parts() -> None:
    expected = sha1("aabbccdd".encode("utf-8")).hexdigest()

    assert build_wechat_msg_signature("dd", "aa", "cc", "bb") == expected


def test_encrypt_and_decrypt_wechat_message_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.wechat_official_account_crypto.os.urandom",
        lambda _: b"0123456789ABCDEF",
    )
    plaintext = "<xml><Content><![CDATA[test]]></Content></xml>"

    encrypted = encrypt_wechat_message(
        plaintext=plaintext,
        app_id=APP_ID,
        encoding_aes_key=ENCODING_AES_KEY,
    )

    assert (
        decrypt_wechat_message(
            encrypted=encrypted,
            app_id=APP_ID,
            encoding_aes_key=ENCODING_AES_KEY,
        )
        == plaintext
    )


def test_decrypt_wechat_message_rejects_wrong_app_id() -> None:
    plaintext = "<xml><Content><![CDATA[test]]></Content></xml>"
    encrypted = encrypt_wechat_message(
        plaintext=plaintext,
        app_id=APP_ID,
        encoding_aes_key=ENCODING_AES_KEY,
    )

    with pytest.raises(WeChatOfficialAccountCryptoError, match="wechat app id mismatch"):
        decrypt_wechat_message(
            encrypted=encrypted,
            app_id="wx-wrong-appid",
            encoding_aes_key=ENCODING_AES_KEY,
        )


def test_wechat_aes_helper_sign_requires_only_signature_arguments() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(HELPER_PATH),
            "sign",
            "--value",
            "encrypted-payload",
            "--token",
            "wechat-token",
            "--timestamp",
            "1710000000",
            "--nonce",
            "nonce-123",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == build_wechat_msg_signature(
        "wechat-token",
        "1710000000",
        "nonce-123",
        "encrypted-payload",
    )


def test_wechat_aes_helper_encrypt_and_decrypt_round_trip() -> None:
    plaintext = "<xml><Content><![CDATA[helper test]]></Content></xml>"
    encrypt_result = subprocess.run(
        [
            sys.executable,
            str(HELPER_PATH),
            "encrypt",
            "--value",
            plaintext,
            "--app-id",
            APP_ID,
            "--encoding-aes-key",
            ENCODING_AES_KEY,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert encrypt_result.returncode == 0
    encrypted = encrypt_result.stdout.strip()
    assert encrypted

    decrypt_result = subprocess.run(
        [
            sys.executable,
            str(HELPER_PATH),
            "decrypt",
            "--value",
            encrypted,
            "--app-id",
            APP_ID,
            "--encoding-aes-key",
            ENCODING_AES_KEY,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert decrypt_result.returncode == 0
    assert decrypt_result.stdout.strip() == plaintext


def test_wechat_aes_helper_encrypt_reports_missing_app_id() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(HELPER_PATH),
            "encrypt",
            "--value",
            "<xml></xml>",
            "--encoding-aes-key",
            ENCODING_AES_KEY,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "encrypt requires --app-id" in result.stderr
