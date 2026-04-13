from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.content import SchoolContentVersion


def publish_school_version(
    session: Session, school_id: int, version_id: int, operator: str
) -> SchoolContentVersion:
    stmt = select(SchoolContentVersion).where(
        SchoolContentVersion.id == version_id,
        SchoolContentVersion.school_id == school_id,
    )
    version = session.exec(stmt).one()

    published_stmt = select(SchoolContentVersion).where(
        SchoolContentVersion.school_id == school_id,
        SchoolContentVersion.status == "published",
        SchoolContentVersion.id != version_id,
    )
    published_versions = session.exec(published_stmt).all()
    for published in published_versions:
        published.status = "archived"

    version.status = "published"
    version.published_by = operator
    version.published_at = datetime.now(timezone.utc)

    session.add(version)
    return version
