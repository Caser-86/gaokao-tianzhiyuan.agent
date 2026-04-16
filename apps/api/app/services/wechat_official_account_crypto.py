import base64
import os
import struct
from hashlib import sha1

import pyaes


class WeChatOfficialAccountCryptoError(ValueError):
    pass


def build_wechat_msg_signature(*parts: str) -> str:
    payload = "".join(sorted(parts))
    return sha1(payload.encode("utf-8")).hexdigest()


def _decode_encoding_aes_key(encoding_aes_key: str) -> bytes:
    try:
        key = base64.b64decode(f"{encoding_aes_key}=")
    except Exception as exc:  # pragma: no cover - defensive path
        raise WeChatOfficialAccountCryptoError("invalid encoding aes key") from exc

    if len(key) != 32:
        raise WeChatOfficialAccountCryptoError("invalid encoding aes key")

    return key


def _pad_wechat_plaintext(raw: bytes) -> bytes:
    block_size = 32
    amount = block_size - (len(raw) % block_size)
    if amount == 0:
        amount = block_size
    return raw + bytes([amount]) * amount


def _unpad_wechat_plaintext(raw: bytes) -> bytes:
    if not raw:
        raise WeChatOfficialAccountCryptoError("invalid encrypted payload")

    amount = raw[-1]
    if amount < 1 or amount > 32:
        raise WeChatOfficialAccountCryptoError("invalid encrypted payload")

    return raw[:-amount]


def encrypt_wechat_message(
    *,
    plaintext: str,
    app_id: str,
    encoding_aes_key: str,
) -> str:
    key = _decode_encoding_aes_key(encoding_aes_key)
    iv = key[:16]
    plaintext_bytes = plaintext.encode("utf-8")
    raw = (
        os.urandom(16)
        + struct.pack(">I", len(plaintext_bytes))
        + plaintext_bytes
        + app_id.encode("utf-8")
    )
    padded = _pad_wechat_plaintext(raw)
    encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(key, iv=iv))
    encrypted = encrypter.feed(padded) + encrypter.feed()
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_wechat_message(
    *,
    encrypted: str,
    app_id: str,
    encoding_aes_key: str,
) -> str:
    key = _decode_encoding_aes_key(encoding_aes_key)
    iv = key[:16]

    try:
        encrypted_bytes = base64.b64decode(encrypted)
    except Exception as exc:  # pragma: no cover - defensive path
        raise WeChatOfficialAccountCryptoError("invalid encrypted payload") from exc

    decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv=iv))
    padded = decrypter.feed(encrypted_bytes) + decrypter.feed()
    plain = _unpad_wechat_plaintext(padded)
    if len(plain) < 20:
        raise WeChatOfficialAccountCryptoError("invalid encrypted payload")

    xml_length = struct.unpack(">I", plain[16:20])[0]
    xml_end = 20 + xml_length
    xml_content = plain[20:xml_end].decode("utf-8")
    app_id_from_payload = plain[xml_end:].decode("utf-8")
    if app_id_from_payload != app_id:
        raise WeChatOfficialAccountCryptoError("wechat app id mismatch")

    return xml_content
