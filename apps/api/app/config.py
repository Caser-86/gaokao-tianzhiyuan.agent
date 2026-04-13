from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAOKAO_AGENT_")

    app_name: str = "gaokao-agent-api"
    api_prefix: str = "/api"


settings = Settings()
