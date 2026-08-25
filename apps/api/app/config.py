import json
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_ADMIN_TOKEN = "dev-admin-token"
SAFE_DEFAULT_ADMIN_TOKEN_ENVIRONMENTS = {"development", "test"}
DEFAULT_SESSION_SECRET = "dev-session-secret"
DEFAULT_SESSION_TTL_SECONDS = 60 * 60 * 24 * 30
DEFAULT_WECHAT_SIGNATURE_TTL_SECONDS = 300
DEFAULT_WECHAT_MAX_BODY_BYTES = 256 * 1024
DEFAULT_CHAT_SESSION_RETENTION_DAYS = 30
DEFAULT_MEDIA_ANALYSIS_RETENTION_DAYS = 30
DEFAULT_AGENT_TRACE_RETENTION_DAYS = 7
DEFAULT_CORS_ALLOWED_ORIGINS = (
    "http://127.0.0.1:3000",
    "http://localhost:3000",
)
DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES = (
    Path(__file__).resolve().parents[3] / "vendor" / "zhangxuefeng-skill" / "SKILL.md",
    Path(__file__).resolve().parents[3] / ".tmp" / "zhangxuefeng-skill" / "SKILL.md",
)


def resolve_zhangxuefeng_skill_path(
    configured_path: str,
    *,
    default_candidates: Sequence[Path] = DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES,
) -> str:
    normalized = configured_path.strip()
    if normalized and Path(normalized).is_file():
        return normalized

    for candidate in default_candidates:
        if candidate.is_file():
            return str(candidate)

    return normalized


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GAOKAO_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "gaokao-agent-api"
    release_version: str = "dev"
    api_prefix: str = "/api"
    environment: str = "development"
    admin_token: str = DEFAULT_ADMIN_TOKEN
    session_secret: str = DEFAULT_SESSION_SECRET
    session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS
    wechat_signature_ttl_seconds: int = DEFAULT_WECHAT_SIGNATURE_TTL_SECONDS
    wechat_max_body_bytes: int = DEFAULT_WECHAT_MAX_BODY_BYTES
    chat_session_retention_days: int = DEFAULT_CHAT_SESSION_RETENTION_DAYS
    media_analysis_retention_days: int = DEFAULT_MEDIA_ANALYSIS_RETENTION_DAYS
    agent_trace_retention_days: int = DEFAULT_AGENT_TRACE_RETENTION_DAYS
    database_url: str = "sqlite:///./gaokao-agent.db"
    cors_allowed_origins: Annotated[tuple[str, ...], NoDecode] = DEFAULT_CORS_ALLOWED_ORIGINS
    llm_provider: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 30
    media_analysis_provider: str = ""
    media_analysis_base_url: str = ""
    media_analysis_api_key: str = ""
    media_analysis_model: str = ""
    media_analysis_timeout_seconds: int = 30
    zhangxuefeng_skill_path: str = ""
    smart_analysis_mode: str = "off"
    wechat_official_account_token: str = ""
    wechat_official_account_app_id: str = ""
    wechat_official_account_encoding_aes_key: str = ""

    @field_validator("smart_analysis_mode")
    @classmethod
    def validate_smart_analysis_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"off", "gated", "on"}:
            raise ValueError("smart_analysis_mode must be one of: off, gated, on")
        return normalized

    @field_validator("media_analysis_provider")
    @classmethod
    def validate_media_analysis_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"", "pending", "noop", "none", "openai_compatible"}:
            raise ValueError(
                "media_analysis_provider must be one of: '', pending, noop, none, openai_compatible"
            )
        return normalized

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def validate_cors_allowed_origins(cls, value: str | Sequence[str] | None) -> tuple[str, ...]:
        if value is None:
            return DEFAULT_CORS_ALLOWED_ORIGINS

        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return ()

            if normalized.startswith("["):
                parsed = json.loads(normalized)
                if not isinstance(parsed, list):
                    raise ValueError("cors_allowed_origins JSON value must be a list")
                return tuple(str(item).strip() for item in parsed if str(item).strip())

            return tuple(item.strip() for item in normalized.split(",") if item.strip())

        return tuple(str(item).strip() for item in value if str(item).strip())

    @field_validator("wechat_official_account_encoding_aes_key")
    @classmethod
    def validate_wechat_official_account_encoding_aes_key(cls, value: str) -> str:
        normalized = value.strip()
        if normalized and len(normalized) != 43:
            raise ValueError("wechat official account encoding aes key must be 43 chars")
        return normalized

    @field_validator(
        "session_ttl_seconds",
        "wechat_signature_ttl_seconds",
        "wechat_max_body_bytes",
        "chat_session_retention_days",
        "media_analysis_retention_days",
        "agent_trace_retention_days",
    )
    @classmethod
    def validate_positive_ttl_or_limit(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("configured TTL, retention, or body limit must be greater than zero")
        return value

    @model_validator(mode="after")
    def validate_admin_token(self) -> "Settings":
        environment = self.environment.strip().lower()
        if (
            self.admin_token == DEFAULT_ADMIN_TOKEN
            and environment not in SAFE_DEFAULT_ADMIN_TOKEN_ENVIRONMENTS
        ):
            raise ValueError("default admin token is only allowed in development/test mode")
        if (
            self.session_secret.strip() in {"", DEFAULT_SESSION_SECRET}
            and environment not in SAFE_DEFAULT_ADMIN_TOKEN_ENVIRONMENTS
        ):
            raise ValueError("default session secret is only allowed in development/test mode")
        return self


settings = Settings()
