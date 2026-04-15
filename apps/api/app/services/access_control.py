from __future__ import annotations

from sqlmodel import Session, select

from ..models.access_control import RuntimeSetting, UserEntitlement

SMART_ANALYSIS_MODE_KEY = "smart_analysis_mode"
SMART_ANALYSIS_ENTITLEMENT = "smart_analysis"
ALLOWED_SMART_ANALYSIS_MODES = {"off", "gated", "on"}


def get_effective_smart_analysis_mode(session: Session, *, default_mode: str) -> str:
    setting = session.get(RuntimeSetting, SMART_ANALYSIS_MODE_KEY)
    if setting is None:
        return default_mode
    return setting.value


def set_smart_analysis_mode(session: Session, mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in ALLOWED_SMART_ANALYSIS_MODES:
        raise ValueError("smart_analysis_mode must be one of: off, gated, on")

    setting = session.get(RuntimeSetting, SMART_ANALYSIS_MODE_KEY)
    if setting is None:
        setting = RuntimeSetting(key=SMART_ANALYSIS_MODE_KEY, value=normalized)
    else:
        setting.value = normalized

    session.add(setting)
    session.commit()
    session.refresh(setting)
    return setting.value


def set_user_entitlement(
    session: Session,
    *,
    user_id: str,
    entitlement: str,
    is_enabled: bool,
) -> UserEntitlement:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id must not be empty")

    statement = select(UserEntitlement).where(
        UserEntitlement.user_id == normalized_user_id,
        UserEntitlement.entitlement == entitlement,
    )
    record = session.exec(statement).one_or_none()
    if record is None:
        record = UserEntitlement(
            user_id=normalized_user_id,
            entitlement=entitlement,
            is_enabled=is_enabled,
        )
    else:
        record.is_enabled = is_enabled

    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_user_entitlements(session: Session, user_id: str) -> list[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []

    statement = select(UserEntitlement).where(
        UserEntitlement.user_id == normalized_user_id,
        UserEntitlement.is_enabled.is_(True),
    )
    return sorted(item.entitlement for item in session.exec(statement).all())
