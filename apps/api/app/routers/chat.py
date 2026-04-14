from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..services.chat import (
    ChatSkillNotFoundError,
    ChatSkillUnavailableError,
    ConversationService,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])
conversation_service = ConversationService()


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
