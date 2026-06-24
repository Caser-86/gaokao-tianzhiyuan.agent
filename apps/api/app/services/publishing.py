from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.content import SchoolContentVersion, VersionStatus


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
        SchoolContentVersion.status == VersionStatus.published,
        SchoolContentVersion.id != version_id,
    )
    published_versions = session.exec(published_stmt).all()
    for published in published_versions:
        published.status = VersionStatus.archived
        session.add(published)

    version.status = VersionStatus.published
    version.published_by = operator
    version.published_at = datetime.now(UTC)

    session.add(version)
    session.flush()
    return version
