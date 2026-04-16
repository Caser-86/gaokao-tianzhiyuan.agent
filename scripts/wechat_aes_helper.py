from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.services.wechat_official_account_crypto import (  # noqa: E402
    WeChatOfficialAccountCryptoError,
    build_wechat_msg_signature,
    decrypt_wechat_message,
    encrypt_wechat_message,
)


def _require_arguments(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    *,
    operation: str,
    argument_names: tuple[str, ...],
) -> None:
    missing: list[str] = []
    for argument_name in argument_names:
        value = getattr(args, argument_name.replace("-", "_"))
        if isinstance(value, str) and value.strip():
            continue
        missing.append(f"--{argument_name}")

    if missing:
        parser.error(f"{operation} requires {' '.join(missing)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="WeChat Official Account AES helper")
    parser.add_argument("operation", choices=("encrypt", "decrypt", "sign"))
    parser.add_argument("--value", required=True)
    parser.add_argument("--app-id", default="")
    parser.add_argument("--encoding-aes-key", default="")
    parser.add_argument("--token", default="")
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--nonce", default="")
    args = parser.parse_args()

    try:
        if args.operation == "encrypt":
            _require_arguments(
                parser,
                args,
                operation="encrypt",
                argument_names=("app-id", "encoding-aes-key"),
            )
            result = encrypt_wechat_message(
                plaintext=args.value,
                app_id=args.app_id,
                encoding_aes_key=args.encoding_aes_key,
            )
        elif args.operation == "decrypt":
            _require_arguments(
                parser,
                args,
                operation="decrypt",
                argument_names=("app-id", "encoding-aes-key"),
            )
            result = decrypt_wechat_message(
                encrypted=args.value,
                app_id=args.app_id,
                encoding_aes_key=args.encoding_aes_key,
            )
        else:
            _require_arguments(
                parser,
                args,
                operation="sign",
                argument_names=("token", "timestamp", "nonce"),
            )
            result = build_wechat_msg_signature(
                args.token,
                args.timestamp,
                args.nonce,
                args.value,
            )
    except WeChatOfficialAccountCryptoError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
