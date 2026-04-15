from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.services.access_control import (
    SMART_ANALYSIS_ENTITLEMENT,
    get_effective_smart_analysis_mode,
    get_user_entitlements,
    set_smart_analysis_mode,
    set_user_entitlement,
)


def build_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_get_effective_smart_analysis_mode_defaults_to_bootstrap_value() -> None:
    with build_session() as session:
        assert (
            get_effective_smart_analysis_mode(session, default_mode="gated") == "gated"
        )


def test_set_smart_analysis_mode_persists_and_overwrites_existing_value() -> None:
    with build_session() as session:
        assert set_smart_analysis_mode(session, "off") == "off"
        assert set_smart_analysis_mode(session, "on") == "on"
        assert get_effective_smart_analysis_mode(session, default_mode="gated") == "on"


def test_set_user_entitlement_grants_and_revokes_smart_analysis() -> None:
    with build_session() as session:
        set_user_entitlement(
            session,
            user_id="wx-openid-1",
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=True,
        )
        assert get_user_entitlements(session, "wx-openid-1") == ["smart_analysis"]

        set_user_entitlement(
            session,
            user_id="wx-openid-1",
            entitlement=SMART_ANALYSIS_ENTITLEMENT,
            is_enabled=False,
        )
        assert get_user_entitlements(session, "wx-openid-1") == []
