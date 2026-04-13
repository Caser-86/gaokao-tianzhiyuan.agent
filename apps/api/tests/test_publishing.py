from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, get_engine
from app.models.content import SchoolContentVersion
from app.services.publishing import publish_school_version


def test_publish_school_version_increments_versions() -> None:
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine, future=True) as session:
        first = publish_school_version(session, "Horizon High", "Initial draft")
        session.commit()
        session.refresh(first)
        assert first.version == 1
        assert first.content == "Initial draft"
        assert first.school.name == "Horizon High"

        second = publish_school_version(session, "Horizon High", "Updated plan")
        session.commit()
        session.refresh(second)
        assert second.version == 2
        assert second.content == "Updated plan"

        saved_versions = session.scalars(
            select(SchoolContentVersion).order_by(SchoolContentVersion.version)
        ).all()
        assert len(saved_versions) == 2
        assert saved_versions[0].version == 1
        assert saved_versions[1].version == 2
        assert saved_versions[0].content == "Initial draft"
        assert saved_versions[1].content == "Updated plan"
