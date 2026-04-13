from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content import School, SchoolContentVersion


def publish_school_version(
    session: Session, school_name: str, content: str
) -> SchoolContentVersion:
    """
    Record a new published content version for the given school name.
    """

    school = session.scalar(select(School).where(School.name == school_name))
    if school is None:
        school = School(name=school_name)
        session.add(school)
        session.flush()

    highest_version = session.scalar(
        select(func.max(SchoolContentVersion.version)).where(
            SchoolContentVersion.school_id == school.id
        )
    )
    next_version = (highest_version or 0) + 1

    version = SchoolContentVersion(
        school=school,
        version=next_version,
        content=content,
    )
    session.add(version)
    session.flush()
    session.refresh(version, attribute_names=["school"])
    return version
