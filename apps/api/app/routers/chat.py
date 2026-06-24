from hashlib import sha1
from time import time
from typing import Any, Literal
from xml.etree import ElementTree

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session

from ..config import settings
from ..db import get_engine
from ..services.chat import (
    ChatSkillNotFoundError,
    ChatSkillUnavailableError,
    ConversationService,
)
from ..services.media_analysis import (
    MediaAnalysisRequest,
    MediaAnalysisResult,
    build_media_analysis_provider,
    resolve_media_analysis_access,
)
from ..services.media_analysis_events import create_media_analysis_event
from ..services.wechat_official_account_crypto import (
    WeChatOfficialAccountCryptoError,
    build_wechat_msg_signature,
    decrypt_wechat_message,
    encrypt_wechat_message,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])
conversation_service = ConversationService()
media_analysis_provider = build_media_analysis_provider(
    provider=settings.media_analysis_provider,
    base_url=settings.media_analysis_base_url,
    api_key=settings.media_analysis_api_key,
    model=settings.media_analysis_model,
    timeout_seconds=settings.media_analysis_timeout_seconds,
)
WECHAT_OFFICIAL_ACCOUNT_MENU_FALLBACK_REPLY = "\u8be5\u83dc\u5355\u529f\u80fd\u8fd8\u5728\u6574\u7406\u4e2d\uff0c\u4f60\u4e5f\u53ef\u4ee5\u76f4\u63a5\u53d1\u9001\u95ee\u9898\u7ed9\u6211\u3002"
WECHAT_OFFICIAL_ACCOUNT_MENU_USAGE_HELP_REPLY = "\u4f60\u53ef\u4ee5\u76f4\u63a5\u53d1\u9001\u7701\u4efd\u3001\u5206\u6570\u3001\u9009\u79d1\u548c\u76ee\u6807\u4e13\u4e1a\uff0c\u6211\u4f1a\u7ee7\u7eed\u5e2e\u4f60\u5206\u6790\u3002"
WECHAT_OFFICIAL_ACCOUNT_PICTURE_FALLBACK_REPLY = "\u5df2\u6536\u5230\u4f60\u4e0a\u4f20\u7684\u56fe\u7247\u3002\u5f53\u524d\u516c\u4f17\u53f7\u56de\u8c03\u8fd8\u4e0d\u652f\u6301\u76f4\u63a5\u8bc6\u56fe\uff0c\u8bf7\u7ee7\u7eed\u8865\u5145\u6587\u5b57\u63cf\u8ff0\u3001\u5206\u6570\u3001\u7701\u4efd\u6216\u4e13\u4e1a\u65b9\u5411\uff0c\u6211\u7ee7\u7eed\u5e2e\u4f60\u5206\u6790\u3002"
WECHAT_OFFICIAL_ACCOUNT_WELCOME_REPLY = "\u6b22\u8fce\u5173\u6ce8\u9ad8\u8003Agent\uff0c\u8bf7\u76f4\u63a5\u53d1\u9001\u7701\u4efd\u3001\u5206\u6570\u3001\u9009\u79d1\u548c\u76ee\u6807\u4e13\u4e1a\uff0c\u6211\u6765\u5e2e\u4f60\u505a\u5fd7\u613f\u5206\u6790\u3002"
WECHAT_OFFICIAL_ACCOUNT_UNSUPPORTED_REPLY = "\u5f53\u524d\u5df2\u652f\u6301\u6587\u672c\u6d88\u606f\u3001\u5173\u6ce8\u4e8b\u4ef6\u548c\u5e38\u7528\u83dc\u5355\u4e8b\u4ef6\uff0c\u5176\u4ed6\u7c7b\u578b\u540e\u7eed\u5f00\u653e\u3002"
WECHAT_OFFICIAL_ACCOUNT_EMPTY_TEXT_REPLY = "\u6d88\u606f\u4e0d\u80fd\u4e3a\u7a7a\uff0c\u8bf7\u76f4\u63a5\u53d1\u9001\u5206\u6570\u3001\u5730\u533a\u6216\u4e13\u4e1a\u65b9\u5411\u3002"
WECHAT_OFFICIAL_ACCOUNT_SKILL_NOT_FOUND_REPLY = "\u5f53\u524d\u6682\u672a\u5339\u914d\u5230\u53ef\u7528\u670d\u52a1\uff0c\u8bf7\u6362\u4e2a\u95ee\u6cd5\u8bd5\u8bd5\u3002"
WECHAT_OFFICIAL_ACCOUNT_SKILL_UNAVAILABLE_REPLY = "\u5f53\u524d\u54a8\u8be2\u670d\u52a1\u6682\u4e0d\u53ef\u7528\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002"
WECHAT_OFFICIAL_ACCOUNT_DEFAULT_REPLY = "\u5df2\u6536\u5230\u4f60\u7684\u6d88\u606f\u3002"
WECHAT_OFFICIAL_ACCOUNT_VOICE_FALLBACK_REPLY = "\u5f53\u524d\u6536\u5230\u7684\u662f\u8bed\u97f3\u6d88\u606f\u3002\u5982\u679c\u516c\u4f17\u53f7\u5df2\u5f00\u542f\u8bed\u97f3\u8bc6\u522b\uff0c\u6211\u4f1a\u4f18\u5148\u8bfb\u53d6\u8bc6\u522b\u6587\u672c\u7ee7\u7eed\u5206\u6790\uff1b\u5982\u679c\u6ca1\u8bc6\u522b\u51fa\u6765\uff0c\u8bf7\u76f4\u63a5\u53d1\u9001\u6587\u5b57\u3002"
WECHAT_OFFICIAL_ACCOUNT_VIDEO_FALLBACK_REPLY = "\u5df2\u6536\u5230\u4f60\u53d1\u9001\u7684\u89c6\u9891\u3002\u5f53\u524d\u516c\u4f17\u53f7\u56de\u8c03\u8fd8\u4e0d\u652f\u6301\u76f4\u63a5\u5206\u6790\u89c6\u9891\u5185\u5bb9\uff0c\u8bf7\u7ee7\u7eed\u8865\u5145\u6587\u5b57\u63cf\u8ff0\u3001\u5206\u6570\u3001\u7701\u4efd\u6216\u4e13\u4e1a\u65b9\u5411\uff0c\u6211\u7ee7\u7eed\u5e2e\u4f60\u5206\u6790\u3002"
WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_PENDING_REPLY = "\u5df2\u6536\u5230\u4f60\u7684\u5a92\u4f53\u6d88\u606f\u3002\u5f53\u524d\u4f60\u7684\u667a\u80fd\u5206\u6790\u6743\u9650\u5df2\u7ecf\u5f00\u542f\uff0c\u4f46\u516c\u4f17\u53f7\u901a\u9053\u8fd8\u672a\u63a5\u5165\u56fe\u7247\u6216\u89c6\u9891\u89e3\u6790\u5f15\u64ce\u3002\u8bf7\u7ee7\u7eed\u8865\u5145\u6587\u5b57\u63cf\u8ff0\u3001\u5206\u6570\u3001\u7701\u4efd\u6216\u4e13\u4e1a\u65b9\u5411\uff0c\u6211\u53ef\u4ee5\u5148\u7ee7\u7eed\u5e2e\u4f60\u5206\u6790\u3002"
WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_UNAVAILABLE_REPLY = "\u5df2\u6536\u5230\u4f60\u4e0a\u4f20\u7684\u56fe\u7247\uff0c\u4f46\u5f53\u524d\u56fe\u7247\u89e3\u6790\u6682\u65f6\u4e0d\u53ef\u7528\u3002\u8bf7\u7ee7\u7eed\u8865\u5145\u6587\u5b57\u63cf\u8ff0\u3001\u5206\u6570\u3001\u7701\u4efd\u6216\u4e13\u4e1a\u65b9\u5411\uff0c\u6211\u5148\u7ee7\u7eed\u5e2e\u4f60\u5206\u6790\u3002"
WECHAT_OFFICIAL_ACCOUNT_MENU_KEY_CONFIG: dict[str, dict[str, str]] = {
    "menu_usage_help": {
        "mode": "reply_only",
        "reply_text": WECHAT_OFFICIAL_ACCOUNT_MENU_USAGE_HELP_REPLY,
    },
    "menu_score_assessment": {
        "mode": "chat_prompt",
        "prompt": "\u8bf7\u5e2e\u6211\u505a\u5206\u6570\u5b9a\u4f4d\u3002",
    },
    "menu_major_recommendation": {
        "mode": "chat_prompt",
        "prompt": "\u8bf7\u7ed9\u6211\u505a\u4e13\u4e1a\u63a8\u8350\u3002",
    },
    "menu_volunteer_strategy": {
        "mode": "chat_prompt",
        "prompt": "\u8bf7\u7ed9\u6211\u4e00\u4efd\u5fd7\u613f\u586b\u62a5\u7b56\u7565\u5efa\u8bae\u3002",
    },
}


class ChatMessageRequest(BaseModel):
    channel: Literal["wechat", "web"]
    user_id: str
    message: str
    session_id: str | None = None
    skill_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_id", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


class DirectSkillInvokeRequest(BaseModel):
    channel: Literal["wechat", "web"]
    user_id: str
    message: str
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_id", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


class WeChatChannelRequest(BaseModel):
    openid: str
    message: str
    message_type: str = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("openid", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


def _get_wechat_official_account_token() -> str:
    token = settings.wechat_official_account_token.strip()
    if not token:
        raise HTTPException(
            status_code=503,
            detail="wechat official account token not configured",
        )
    return token


def _get_wechat_official_account_aes_settings() -> tuple[str, str]:
    app_id = settings.wechat_official_account_app_id.strip()
    encoding_aes_key = settings.wechat_official_account_encoding_aes_key.strip()
    if not app_id or not encoding_aes_key:
        raise HTTPException(
            status_code=503,
            detail="wechat official account aes settings not configured",
        )
    return app_id, encoding_aes_key


def _verify_wechat_signature(*, signature: str, timestamp: str, nonce: str) -> None:
    token = _get_wechat_official_account_token()
    payload = "".join(sorted([token, timestamp, nonce]))
    expected = sha1(payload.encode("utf-8")).hexdigest()
    if signature != expected:
        raise HTTPException(
            status_code=403,
            detail="wechat signature verification failed",
        )


def _verify_wechat_aes_signature(
    *,
    msg_signature: str,
    timestamp: str,
    nonce: str,
    encrypted: str,
) -> None:
    token = _get_wechat_official_account_token()
    expected = build_wechat_msg_signature(token, timestamp, nonce, encrypted)
    if msg_signature != expected:
        raise HTTPException(
            status_code=403,
            detail="wechat signature verification failed",
        )


def _parse_wechat_xml_node(node: ElementTree.Element) -> Any:
    children = list(node)
    if not children:
        return (node.text or "").strip()

    payload: dict[str, Any] = {}
    for child in children:
        payload[child.tag] = _parse_wechat_xml_node(child)

    return payload


def _parse_wechat_xml_payload(raw_body: bytes) -> dict[str, Any]:
    try:
        root = ElementTree.fromstring(raw_body)
    except ElementTree.ParseError as exc:
        raise HTTPException(status_code=400, detail="invalid wechat xml payload") from exc

    payload: dict[str, Any] = {}
    for child in root:
        payload[child.tag] = _parse_wechat_xml_node(child)

    if not payload.get("FromUserName") or not payload.get("ToUserName"):
        raise HTTPException(status_code=400, detail="missing wechat xml identity fields")

    return payload


def _extract_wechat_encrypted_payload(raw_body: bytes) -> str:
    try:
        root = ElementTree.fromstring(raw_body)
    except ElementTree.ParseError as exc:
        raise HTTPException(status_code=400, detail="invalid wechat xml payload") from exc

    encrypted = ""
    for child in root:
        if child.tag == "Encrypt":
            encrypted = (child.text or "").strip()
            break

    if not encrypted:
        raise HTTPException(status_code=400, detail="missing wechat encrypted payload")
    return encrypted


def _wechat_cdata(value: str) -> str:
    return value.replace("]]>", "]]]]><![CDATA[>")


def _build_wechat_passive_reply(*, to_user: str, from_user: str, content: str) -> str:
    return (
        "<xml>"
        f"<ToUserName><![CDATA[{_wechat_cdata(to_user)}]]></ToUserName>"
        f"<FromUserName><![CDATA[{_wechat_cdata(from_user)}]]></FromUserName>"
        f"<CreateTime>{int(time())}</CreateTime>"
        "<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{_wechat_cdata(content)}]]></Content>"
        "</xml>"
    )


def _build_wechat_passive_xml_response(*, to_user: str, from_user: str, content: str) -> Response:
    return Response(
        content=_build_wechat_passive_reply(
            to_user=to_user,
            from_user=from_user,
            content=content,
        ),
        media_type="application/xml",
    )


def _build_wechat_aes_xml_response(
    *,
    plaintext_xml: str,
    timestamp: str,
    nonce: str,
) -> Response:
    app_id, encoding_aes_key = _get_wechat_official_account_aes_settings()
    encrypted = encrypt_wechat_message(
        plaintext=plaintext_xml,
        app_id=app_id,
        encoding_aes_key=encoding_aes_key,
    )
    msg_signature = build_wechat_msg_signature(
        _get_wechat_official_account_token(),
        timestamp,
        nonce,
        encrypted,
    )
    content = (
        "<xml>"
        f"<Encrypt><![CDATA[{_wechat_cdata(encrypted)}]]></Encrypt>"
        f"<MsgSignature><![CDATA[{_wechat_cdata(msg_signature)}]]></MsgSignature>"
        f"<TimeStamp>{_wechat_cdata(timestamp)}</TimeStamp>"
        f"<Nonce><![CDATA[{_wechat_cdata(nonce)}]]></Nonce>"
        "</xml>"
    )
    return Response(content=content, media_type="application/xml")


def _build_wechat_official_account_metadata(
    *,
    to_user: str,
    message_type: str,
    payload: dict[str, Any],
    source: str = "wechat_official_account",
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "source": source,
        "message_type": message_type,
        "wechat_official_account": {
            "to_user_name": to_user,
            "msg_id": payload.get("MsgId", ""),
            "create_time": payload.get("CreateTime", ""),
        },
    }

    event_type = payload.get("Event", "").lower()
    event_key = str(payload.get("EventKey", ""))
    if event_type:
        metadata["wechat_official_account"]["event"] = event_type
    if event_key:
        metadata["wechat_official_account"]["event_key"] = event_key

    return metadata


def _route_wechat_official_account_event_into_chat(
    *,
    from_user: str,
    message: str,
    metadata: dict[str, Any],
) -> str:
    try:
        result = conversation_service.handle_message(
            channel="wechat",
            user_id=from_user,
            message=message,
            metadata=metadata,
        )
    except ChatSkillNotFoundError:
        return WECHAT_OFFICIAL_ACCOUNT_SKILL_NOT_FOUND_REPLY
    except ChatSkillUnavailableError:
        return WECHAT_OFFICIAL_ACCOUNT_SKILL_UNAVAILABLE_REPLY

    content = result.get("output", {}).get("content", {})
    return (
        content.get("rendered_reply")
        or content.get("summary")
        or WECHAT_OFFICIAL_ACCOUNT_DEFAULT_REPLY
    )


def _handle_wechat_official_account_menu_click(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
) -> str:
    event_key = str(payload.get("EventKey", ""))
    config = WECHAT_OFFICIAL_ACCOUNT_MENU_KEY_CONFIG.get(event_key)
    if not config:
        return WECHAT_OFFICIAL_ACCOUNT_MENU_FALLBACK_REPLY

    if config["mode"] == "reply_only":
        return config["reply_text"]

    return _route_wechat_official_account_event_into_chat(
        from_user=from_user,
        message=config["prompt"],
        metadata=_build_wechat_official_account_metadata(
            to_user=to_user,
            message_type="event",
            payload=payload,
            source="wechat_official_account_menu_click",
        ),
    )


def _handle_wechat_official_account_scan_event(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
) -> str:
    scan_info = payload.get("ScanCodeInfo")
    if not isinstance(scan_info, dict):
        return WECHAT_OFFICIAL_ACCOUNT_MENU_FALLBACK_REPLY

    scan_type = str(scan_info.get("ScanType", "")).strip()
    scan_result = str(scan_info.get("ScanResult", "")).strip()
    if not scan_result:
        return WECHAT_OFFICIAL_ACCOUNT_MENU_FALLBACK_REPLY

    metadata = _build_wechat_official_account_metadata(
        to_user=to_user,
        message_type="event",
        payload=payload,
        source="wechat_official_account_event",
    )
    metadata["wechat_official_account"]["scan_type"] = scan_type
    metadata["wechat_official_account"]["scan_result"] = scan_result

    return _route_wechat_official_account_event_into_chat(
        from_user=from_user,
        message=f"\u6211\u521a\u521a\u626b\u7801\u4e86\uff0c\u7ed3\u679c\u662f\uff1a{scan_result}",
        metadata=metadata,
    )


def _handle_wechat_official_account_location_event(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
) -> str:
    location_info = payload.get("SendLocationInfo")
    if not isinstance(location_info, dict):
        return WECHAT_OFFICIAL_ACCOUNT_MENU_FALLBACK_REPLY

    label = str(location_info.get("Label", "")).strip()
    if not label:
        return WECHAT_OFFICIAL_ACCOUNT_MENU_FALLBACK_REPLY

    metadata = _build_wechat_official_account_metadata(
        to_user=to_user,
        message_type="event",
        payload=payload,
        source="wechat_official_account_event",
    )
    metadata["wechat_official_account"]["location_label"] = label
    metadata["wechat_official_account"]["location_name"] = str(
        location_info.get("Poiname", "")
    ).strip()
    metadata["wechat_official_account"]["location_x"] = str(
        location_info.get("Location_X", "")
    ).strip()
    metadata["wechat_official_account"]["location_y"] = str(
        location_info.get("Location_Y", "")
    ).strip()
    metadata["wechat_official_account"]["scale"] = str(location_info.get("Scale", "")).strip()

    return _route_wechat_official_account_event_into_chat(
        from_user=from_user,
        message=f"\u6211\u9009\u62e9\u7684\u4f4d\u7f6e\u662f\uff1a{label}",
        metadata=metadata,
    )


def _handle_wechat_official_account_picture_event(payload: dict[str, Any]) -> str:
    picture_info = payload.get("SendPicsInfo")
    if not isinstance(picture_info, dict):
        return WECHAT_OFFICIAL_ACCOUNT_PICTURE_FALLBACK_REPLY

    count = str(picture_info.get("Count", "")).strip()
    if count and count.isdigit():
        return (
            f"\u5df2\u6536\u5230\u4f60\u4e0a\u4f20\u7684{count}\u5f20\u56fe\u7247\u3002\u5f53\u524d\u516c\u4f17\u53f7\u56de\u8c03\u8fd8\u4e0d\u652f\u6301\u76f4\u63a5\u8bc6\u56fe\uff0c"
            "\u8bf7\u7ee7\u7eed\u8865\u5145\u6587\u5b57\u63cf\u8ff0\u3001\u5206\u6570\u3001\u7701\u4efd\u6216\u4e13\u4e1a\u65b9\u5411\uff0c\u6211\u7ee7\u7eed\u5e2e\u4f60\u5206\u6790\u3002"
        )

    return WECHAT_OFFICIAL_ACCOUNT_PICTURE_FALLBACK_REPLY


def _is_wechat_official_account_media_analysis_enabled(user_id: str) -> bool:
    with Session(get_engine()) as session:
        decision = resolve_media_analysis_access(
            session,
            user_id=user_id,
            default_mode=settings.smart_analysis_mode,
        )
    return decision.enabled


def _run_wechat_official_account_media_analysis(
    *,
    media_type: Literal["image", "video", "shortvideo"],
    from_user: str,
    payload: dict[str, Any],
) -> MediaAnalysisResult:
    return media_analysis_provider.analyze(
        request=MediaAnalysisRequest(
            media_type=media_type,
            user_id=from_user,
            payload=payload,
        )
    )


def _build_media_analysis_chat_message(extracted_fields: dict[str, Any]) -> str | None:
    province = str(extracted_fields.get("province", "")).strip()
    subject = str(extracted_fields.get("subject", "")).strip()
    target_major = str(extracted_fields.get("target_major", "")).strip()
    target_school = str(extracted_fields.get("target_school", "")).strip()
    score = extracted_fields.get("score")
    rank = extracted_fields.get("rank")

    score_text = ""
    if isinstance(score, int | float):
        score_text = f"{int(score)}\u5206"
    elif isinstance(score, str) and score.strip():
        score_text = f"{score.strip()}\u5206"

    rank_text = ""
    if isinstance(rank, int | float):
        rank_text = f"\u4f4d\u6b21{int(rank)}"
    elif isinstance(rank, str) and rank.strip():
        rank_text = f"\u4f4d\u6b21{rank.strip()}"

    if not province or not (score_text or rank_text) or not (target_major or target_school):
        return None

    segments = [province]
    if subject:
        segments.append(subject)
    if score_text:
        segments.append(score_text)
    if rank_text:
        segments.append(rank_text)

    message = "".join(segments)
    if target_major:
        message += f"\uff0c\u76ee\u6807\u4e13\u4e1a{target_major}"
    if target_school:
        message += f"\uff0c\u76ee\u6807\u9662\u6821{target_school}"
    message += "\u3002\u8bf7\u5e2e\u6211\u505a\u9ad8\u8003\u5fd7\u613f\u5206\u6790\u3002"
    return message


def _build_wechat_official_account_media_analysis_context(
    payload: dict[str, Any],
) -> dict[str, str]:
    context: dict[str, str] = {}
    field_mappings = (
        ("ToUserName", "to_user_name"),
        ("FromUserName", "from_user_name"),
        ("CreateTime", "create_time"),
        ("MsgType", "msg_type"),
        ("MsgId", "msg_id"),
        ("MediaId", "media_id"),
        ("PicUrl", "pic_url"),
        ("ThumbMediaId", "thumb_media_id"),
    )

    for payload_key, context_key in field_mappings:
        value = str(payload.get(payload_key, "")).strip()
        if value:
            context[context_key] = value

    return context


def _build_wechat_official_account_media_analysis_event_context(
    *,
    payload: dict[str, Any],
    result: MediaAnalysisResult,
) -> dict[str, str]:
    context = _build_wechat_official_account_media_analysis_context(payload)
    if result.failure_reason:
        context["failure_reason"] = result.failure_reason
    return context


def _route_wechat_official_account_image_media_analysis_into_chat(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
    result: MediaAnalysisResult,
) -> str | None:
    extracted_fields = result.extracted_fields or {}
    if not extracted_fields:
        return None

    message = _build_media_analysis_chat_message(extracted_fields)
    if not message:
        return None

    metadata = _build_wechat_official_account_metadata(
        to_user=to_user,
        message_type="image",
        payload=payload,
        source="wechat_official_account_image_media_analysis",
    )
    metadata["wechat_official_account"]["media_id"] = str(payload.get("MediaId", "")).strip()
    metadata["wechat_official_account"]["pic_url"] = str(payload.get("PicUrl", "")).strip()
    metadata["media_analysis"] = {
        "provider": result.provider,
        "summary": result.summary or "",
        "extracted_fields": extracted_fields,
    }

    return _route_wechat_official_account_event_into_chat(
        from_user=from_user,
        message=message,
        metadata=metadata,
    )


def _record_wechat_official_account_media_analysis_event(
    *,
    from_user: str,
    payload: dict[str, Any],
    media_type: Literal["image", "video", "shortvideo"],
    result: MediaAnalysisResult,
    source: str,
    auto_routed_to_chat: bool,
) -> None:
    with Session(get_engine()) as session:
        create_media_analysis_event(
            session,
            channel="wechat",
            source=source,
            user_id=from_user,
            message_id=str(payload.get("MsgId", "")).strip(),
            media_id=str(payload.get("MediaId", "")).strip(),
            media_type=media_type,
            provider=result.provider,
            status=result.status,
            summary=result.summary or "",
            rendered_reply=result.rendered_reply or "",
            extracted_fields=result.extracted_fields or {},
            context=_build_wechat_official_account_media_analysis_event_context(
                payload=payload,
                result=result,
            ),
            auto_routed_to_chat=auto_routed_to_chat,
        )


def _handle_wechat_official_account_image_message(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
) -> str:
    _ = str(payload.get("MediaId", "")).strip()
    _ = str(payload.get("PicUrl", "")).strip()
    if _is_wechat_official_account_media_analysis_enabled(from_user):
        result = _run_wechat_official_account_media_analysis(
            media_type="image",
            from_user=from_user,
            payload=payload,
        )
        routed_reply = _route_wechat_official_account_image_media_analysis_into_chat(
            from_user=from_user,
            to_user=to_user,
            payload=payload,
            result=result,
        )
        _record_wechat_official_account_media_analysis_event(
            from_user=from_user,
            payload=payload,
            media_type="image",
            result=result,
            source=(
                "wechat_official_account_image_media_analysis"
                if routed_reply
                else "wechat_official_account"
            ),
            auto_routed_to_chat=bool(routed_reply),
        )
        if routed_reply:
            return routed_reply
        if result.status == "success" and result.rendered_reply:
            return result.rendered_reply
        if result.status == "success" and result.summary:
            return result.summary
        if result.status == "failed":
            return WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_UNAVAILABLE_REPLY
        return WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_PENDING_REPLY
    return WECHAT_OFFICIAL_ACCOUNT_PICTURE_FALLBACK_REPLY


def _handle_wechat_official_account_video_message(
    *,
    from_user: str,
    payload: dict[str, Any],
) -> str:
    _ = str(payload.get("MediaId", "")).strip()
    _ = str(payload.get("ThumbMediaId", "")).strip()
    if _is_wechat_official_account_media_analysis_enabled(from_user):
        result = _run_wechat_official_account_media_analysis(
            media_type=str(payload.get("MsgType", "")).strip().lower() or "video",
            from_user=from_user,
            payload=payload,
        )
        _record_wechat_official_account_media_analysis_event(
            from_user=from_user,
            payload=payload,
            media_type=str(payload.get("MsgType", "")).strip().lower() or "video",
            result=result,
            source="wechat_official_account",
            auto_routed_to_chat=False,
        )
        if result.status == "success" and result.rendered_reply:
            return result.rendered_reply
        if result.status == "success" and result.summary:
            return result.summary
        return WECHAT_OFFICIAL_ACCOUNT_VIDEO_FALLBACK_REPLY
    return WECHAT_OFFICIAL_ACCOUNT_VIDEO_FALLBACK_REPLY


def _handle_wechat_official_account_voice_message(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
) -> str:
    recognition = str(payload.get("Recognition", "")).strip()
    if not recognition:
        return WECHAT_OFFICIAL_ACCOUNT_VOICE_FALLBACK_REPLY

    metadata = _build_wechat_official_account_metadata(
        to_user=to_user,
        message_type="voice",
        payload=payload,
        source="wechat_official_account_voice_message",
    )
    metadata["wechat_official_account"]["media_id"] = str(payload.get("MediaId", "")).strip()
    metadata["wechat_official_account"]["format"] = str(payload.get("Format", "")).strip()
    metadata["wechat_official_account"]["recognition"] = recognition

    return _route_wechat_official_account_event_into_chat(
        from_user=from_user,
        message=recognition,
        metadata=metadata,
    )


def _handle_wechat_official_account_location_message(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
) -> str:
    label = str(payload.get("Label", "")).strip()
    location_x = str(payload.get("Location_X", "")).strip()
    location_y = str(payload.get("Location_Y", "")).strip()
    scale = str(payload.get("Scale", "")).strip()

    if not label and not (location_x and location_y):
        return WECHAT_OFFICIAL_ACCOUNT_UNSUPPORTED_REPLY

    metadata = _build_wechat_official_account_metadata(
        to_user=to_user,
        message_type="location",
        payload=payload,
        source="wechat_official_account_location_message",
    )
    metadata["wechat_official_account"]["location_label"] = label
    metadata["wechat_official_account"]["location_x"] = location_x
    metadata["wechat_official_account"]["location_y"] = location_y
    metadata["wechat_official_account"]["scale"] = scale

    message = (
        f"I shared my location: {label}"
        if label
        else f"I shared my location coordinates: {location_x},{location_y}"
    )
    return _route_wechat_official_account_event_into_chat(
        from_user=from_user,
        message=message,
        metadata=metadata,
    )


def _handle_wechat_official_account_link_message(
    *,
    from_user: str,
    to_user: str,
    payload: dict[str, Any],
) -> str:
    title = str(payload.get("Title", "")).strip()
    description = str(payload.get("Description", "")).strip()
    url = str(payload.get("Url", "")).strip()
    if not title and not description and not url:
        return WECHAT_OFFICIAL_ACCOUNT_UNSUPPORTED_REPLY

    metadata = _build_wechat_official_account_metadata(
        to_user=to_user,
        message_type="link",
        payload=payload,
        source="wechat_official_account_link_message",
    )
    metadata["wechat_official_account"]["title"] = title
    metadata["wechat_official_account"]["description"] = description
    metadata["wechat_official_account"]["url"] = url

    message_parts = [
        f"title={title}" if title else "",
        f"description={description}" if description else "",
        f"url={url}" if url else "",
    ]
    message = "I shared a link: " + "; ".join(part for part in message_parts if part)
    return _route_wechat_official_account_event_into_chat(
        from_user=from_user,
        message=message,
        metadata=metadata,
    )


@router.get("/health")
def chat_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/skills")
def list_chat_skills() -> dict[str, list[dict[str, Any]]]:
    return {"items": conversation_service.list_skills()}


@router.post("/messages")
def create_chat_message(payload: ChatMessageRequest) -> dict[str, Any]:
    try:
        return conversation_service.handle_message(
            channel=payload.channel,
            user_id=payload.user_id,
            message=payload.message,
            session_id=payload.session_id,
            skill_id=payload.skill_id,
            metadata=payload.metadata,
        )
    except ChatSkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail="chat skill not found") from exc
    except ChatSkillUnavailableError as exc:
        raise HTTPException(status_code=409, detail="chat skill unavailable") from exc


@router.post("/skills/{skill_id}/invoke")
def invoke_chat_skill(skill_id: str, payload: DirectSkillInvokeRequest) -> dict[str, Any]:
    try:
        return conversation_service.handle_message(
            channel=payload.channel,
            user_id=payload.user_id,
            message=payload.message,
            session_id=payload.session_id,
            skill_id=skill_id,
            metadata=payload.metadata,
        )
    except ChatSkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail="chat skill not found") from exc
    except ChatSkillUnavailableError as exc:
        raise HTTPException(status_code=409, detail="chat skill unavailable") from exc


@router.post("/channels/wechat")
def create_wechat_chat_message(payload: WeChatChannelRequest) -> dict[str, Any]:
    try:
        return conversation_service.handle_message(
            channel="wechat",
            user_id=payload.openid,
            message=payload.message,
            metadata={
                **payload.metadata,
                "message_type": payload.message_type,
            },
        )
    except ChatSkillNotFoundError as exc:
        raise HTTPException(status_code=404, detail="chat skill not found") from exc
    except ChatSkillUnavailableError as exc:
        raise HTTPException(status_code=409, detail="chat skill unavailable") from exc


@router.get(
    "/channels/wechat/official-account",
    response_class=PlainTextResponse,
)
def verify_wechat_official_account(
    timestamp: str,
    nonce: str,
    echostr: str,
    signature: str | None = None,
    msg_signature: str | None = None,
    encrypt_type: str | None = None,
) -> str:
    normalized_encrypt_type = (encrypt_type or "").strip().lower()
    if normalized_encrypt_type == "aes":
        if not msg_signature:
            raise HTTPException(status_code=400, detail="missing wechat msg signature")
        _verify_wechat_aes_signature(
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
            encrypted=echostr,
        )
        app_id, encoding_aes_key = _get_wechat_official_account_aes_settings()
        try:
            return decrypt_wechat_message(
                encrypted=echostr,
                app_id=app_id,
                encoding_aes_key=encoding_aes_key,
            )
        except WeChatOfficialAccountCryptoError as exc:
            raise HTTPException(
                status_code=400,
                detail="invalid wechat encrypted payload",
            ) from exc

    if not signature:
        raise HTTPException(status_code=400, detail="missing wechat signature")
    _verify_wechat_signature(signature=signature, timestamp=timestamp, nonce=nonce)
    return echostr


@router.post("/channels/wechat/official-account")
async def handle_wechat_official_account_message(
    request: Request,
    timestamp: str,
    nonce: str,
    signature: str | None = None,
    msg_signature: str | None = None,
    encrypt_type: str | None = None,
) -> Response:
    normalized_encrypt_type = (encrypt_type or "").strip().lower()
    raw_body = await request.body()
    use_aes = normalized_encrypt_type == "aes"

    if use_aes:
        if not msg_signature:
            raise HTTPException(status_code=400, detail="missing wechat msg signature")
        encrypted = _extract_wechat_encrypted_payload(raw_body)
        _verify_wechat_aes_signature(
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
            encrypted=encrypted,
        )
        app_id, encoding_aes_key = _get_wechat_official_account_aes_settings()
        try:
            decrypted_xml = decrypt_wechat_message(
                encrypted=encrypted,
                app_id=app_id,
                encoding_aes_key=encoding_aes_key,
            )
        except WeChatOfficialAccountCryptoError as exc:
            raise HTTPException(
                status_code=400,
                detail="invalid wechat encrypted payload",
            ) from exc
        payload = _parse_wechat_xml_payload(decrypted_xml.encode("utf-8"))
    else:
        if not signature:
            raise HTTPException(status_code=400, detail="missing wechat signature")
        _verify_wechat_signature(
            signature=signature,
            timestamp=timestamp,
            nonce=nonce,
        )
        payload = _parse_wechat_xml_payload(raw_body)

    from_user = payload["FromUserName"]
    to_user = payload["ToUserName"]
    message_type = payload.get("MsgType", "").lower()
    event_type = payload.get("Event", "").lower()

    if message_type == "event":
        if event_type == "subscribe":
            reply_text = WECHAT_OFFICIAL_ACCOUNT_WELCOME_REPLY
        elif event_type == "unsubscribe":
            return PlainTextResponse("success")
        elif event_type == "click":
            reply_text = _handle_wechat_official_account_menu_click(
                from_user=from_user,
                to_user=to_user,
                payload=payload,
            )
        elif event_type in {"scancode_push", "scancode_waitmsg"}:
            reply_text = _handle_wechat_official_account_scan_event(
                from_user=from_user,
                to_user=to_user,
                payload=payload,
            )
        elif event_type == "location_select":
            reply_text = _handle_wechat_official_account_location_event(
                from_user=from_user,
                to_user=to_user,
                payload=payload,
            )
        elif event_type in {"pic_sysphoto", "pic_photo_or_album", "pic_weixin"}:
            reply_text = _handle_wechat_official_account_picture_event(payload)
        else:
            reply_text = WECHAT_OFFICIAL_ACCOUNT_UNSUPPORTED_REPLY
    elif message_type == "image":
        reply_text = _handle_wechat_official_account_image_message(
            from_user=from_user,
            to_user=to_user,
            payload=payload,
        )
    elif message_type in {"video", "shortvideo"}:
        reply_text = _handle_wechat_official_account_video_message(
            from_user=from_user,
            payload=payload,
        )
    elif message_type == "voice":
        reply_text = _handle_wechat_official_account_voice_message(
            from_user=from_user,
            to_user=to_user,
            payload=payload,
        )
    elif message_type == "location":
        reply_text = _handle_wechat_official_account_location_message(
            from_user=from_user,
            to_user=to_user,
            payload=payload,
        )
    elif message_type == "link":
        reply_text = _handle_wechat_official_account_link_message(
            from_user=from_user,
            to_user=to_user,
            payload=payload,
        )
    elif message_type != "text":
        reply_text = WECHAT_OFFICIAL_ACCOUNT_UNSUPPORTED_REPLY
    else:
        message = payload.get("Content", "")
        if not message:
            reply_text = WECHAT_OFFICIAL_ACCOUNT_EMPTY_TEXT_REPLY
        else:
            try:
                result = conversation_service.handle_message(
                    channel="wechat",
                    user_id=from_user,
                    message=message,
                    metadata=_build_wechat_official_account_metadata(
                        to_user=to_user,
                        message_type=message_type,
                        payload=payload,
                    ),
                )
            except ChatSkillNotFoundError:
                reply_text = WECHAT_OFFICIAL_ACCOUNT_SKILL_NOT_FOUND_REPLY
            except ChatSkillUnavailableError:
                reply_text = WECHAT_OFFICIAL_ACCOUNT_SKILL_UNAVAILABLE_REPLY
            else:
                content = result.get("output", {}).get("content", {})
                reply_text = (
                    content.get("rendered_reply")
                    or content.get("summary")
                    or WECHAT_OFFICIAL_ACCOUNT_DEFAULT_REPLY
                )

    plaintext_response = _build_wechat_passive_reply(
        to_user=from_user,
        from_user=to_user,
        content=reply_text,
    )
    if use_aes:
        return _build_wechat_aes_xml_response(
            plaintext_xml=plaintext_response,
            timestamp=timestamp,
            nonce=nonce,
        )
    return Response(content=plaintext_response, media_type="application/xml")
