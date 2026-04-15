from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ADMIN_TOKEN = "dev-admin-token"
SAFE_DEFAULT_ADMIN_TOKEN_ENVIRONMENTS = {"development", "test"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GAOKAO_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "gaokao-agent-api"
    api_prefix: str = "/api"
    environment: str = "development"
    admin_token: str = DEFAULT_ADMIN_TOKEN
    database_url: str = "sqlite:///./gaokao-agent.db"
    llm_provider: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 30
    zhangxuefeng_skill_path: str = ""
    smart_analysis_mode: str = "off"

    @field_validator("smart_analysis_mode")
    @classmethod
    def validate_smart_analysis_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"off", "gated", "on"}:
            raise ValueError("smart_analysis_mode must be one of: off, gated, on")
        return normalized

    @model_validator(mode="after")
    def validate_admin_token(self) -> "Settings":
        environment = self.environment.strip().lower()
        if (
            self.admin_token == DEFAULT_ADMIN_TOKEN
            and environment not in SAFE_DEFAULT_ADMIN_TOKEN_ENVIRONMENTS
        ):
            raise ValueError(
                "default admin token is only allowed in development/test mode"
            )
        return self


settings = Settings()
