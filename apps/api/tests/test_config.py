import pytest
from pydantic import ValidationError

from app.config import Settings, resolve_zhangxuefeng_skill_path


def test_default_admin_token_is_rejected_outside_safe_modes() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(environment="production", admin_token="dev-admin-token")
    assert "default admin token is only allowed in development/test mode" in str(
        exc_info.value
    )


def test_default_admin_token_is_allowed_in_development_and_test_modes() -> None:
    Settings(environment="development", admin_token="dev-admin-token")
    Settings(environment="test", admin_token="dev-admin-token")


def test_non_default_admin_token_is_allowed_outside_safe_modes() -> None:
    settings = Settings(environment="production", admin_token="task4-custom-token")
    assert settings.admin_token == "task4-custom-token"


def test_settings_can_load_llm_config_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GAOKAO_AGENT_LLM_PROVIDER=openai_compatible",
                "GAOKAO_AGENT_LLM_BASE_URL=https://relay.example",
                "GAOKAO_AGENT_LLM_API_KEY=test-key",
                "GAOKAO_AGENT_LLM_MODEL=gpt-4o-mini",
                "GAOKAO_AGENT_LLM_TIMEOUT_SECONDS=45",
                "GAOKAO_AGENT_ZHANGXUEFENG_SKILL_PATH=D:/skills/zhangxuefeng/SKILL.md",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=str(env_file), _env_file_encoding="utf-8")

    assert settings.llm_provider == "openai_compatible"
    assert settings.llm_base_url == "https://relay.example"
    assert settings.llm_api_key == "test-key"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_timeout_seconds == 45
    assert settings.zhangxuefeng_skill_path == "D:/skills/zhangxuefeng/SKILL.md"


def test_settings_automatically_load_default_dotenv(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GAOKAO_AGENT_LLM_PROVIDER=openai_compatible",
                "GAOKAO_AGENT_LLM_BASE_URL=https://relay.default",
                "GAOKAO_AGENT_LLM_API_KEY=dotenv-key",
                "GAOKAO_AGENT_LLM_MODEL=gpt-4.1-mini",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert settings.llm_provider == "openai_compatible"
    assert settings.llm_base_url == "https://relay.default"
    assert settings.llm_api_key == "dotenv-key"
    assert settings.llm_model == "gpt-4.1-mini"


def test_smart_analysis_mode_accepts_supported_values() -> None:
    assert Settings(smart_analysis_mode="off").smart_analysis_mode == "off"
    assert Settings(smart_analysis_mode="gated").smart_analysis_mode == "gated"
    assert Settings(smart_analysis_mode="on").smart_analysis_mode == "on"


def test_smart_analysis_mode_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(smart_analysis_mode="partial")
    assert "smart_analysis_mode must be one of: off, gated, on" in str(exc_info.value)


def test_resolve_zhangxuefeng_skill_path_prefers_existing_configured_path(
    tmp_path,
) -> None:
    configured_skill = tmp_path / "configured" / "SKILL.md"
    configured_skill.parent.mkdir(parents=True, exist_ok=True)
    configured_skill.write_text("configured", encoding="utf-8")

    fallback_skill = tmp_path / "vendor" / "zhangxuefeng-skill" / "SKILL.md"
    fallback_skill.parent.mkdir(parents=True, exist_ok=True)
    fallback_skill.write_text("fallback", encoding="utf-8")

    assert (
        resolve_zhangxuefeng_skill_path(
            str(configured_skill),
            default_candidates=(fallback_skill,),
        )
        == str(configured_skill)
    )


def test_resolve_zhangxuefeng_skill_path_falls_back_to_first_existing_candidate(
    tmp_path,
) -> None:
    fallback_skill = tmp_path / "vendor" / "zhangxuefeng-skill" / "SKILL.md"
    fallback_skill.parent.mkdir(parents=True, exist_ok=True)
    fallback_skill.write_text("fallback", encoding="utf-8")

    assert (
        resolve_zhangxuefeng_skill_path(
            str(tmp_path / "missing" / "SKILL.md"),
            default_candidates=(fallback_skill,),
        )
        == str(fallback_skill)
    )
