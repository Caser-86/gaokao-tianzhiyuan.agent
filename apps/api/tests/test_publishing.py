from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine

from app.models.content import School, SchoolContentVersion
from app.services.publishing import publish_school_version


def test_publish_school_version_marks_only_target_version_published() -> None:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        school = School(name="示例大学", slug="example-university")
        session.add(school)
        session.commit()
        session.refresh(school)

        now = datetime.now(timezone.utc)
        old_version = SchoolContentVersion(
            school_id=school.id,
            version=1,
            summary="old",
            status="published",
            published_at=now,
            published_by="author",
        )
        new_version = SchoolContentVersion(
            school_id=school.id,
            version=2,
            summary="new",
            status="draft",
        )

        session.add_all([old_version, new_version])
        session.commit()
        session.refresh(old_version)
        session.refresh(new_version)

        published = publish_school_version(
            session, school.id, new_version.id, operator="editor"
        )
        session.commit()
        session.refresh(old_version)
        session.refresh(new_version)

        assert old_version.version == 1
        assert new_version.version == 2
        assert old_version.status == "archived"
        assert new_version.status == "published"
        assert new_version.published_by == "editor"
        assert new_version.published_at is not None
        assert published.id == new_version.id
