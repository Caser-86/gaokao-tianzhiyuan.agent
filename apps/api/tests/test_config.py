import pytest
from pydantic import ValidationError

from app.config import Settings


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
