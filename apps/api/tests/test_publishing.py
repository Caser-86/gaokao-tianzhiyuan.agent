from datetime import datetime, timezone

from sqlmodel import Session, create_engine

from app.db import create_all_models, get_engine
from app.models.content import School, SchoolContentVersion
from app.services.publishing import publish_school_version


def test_publish_school_version_marks_only_target_version_published() -> None:
    engine = get_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    create_all_models(engine)

    with Session(engine) as session:
        school = School(name="Example University", slug="example-university")
        session.add(school)
        session.commit()
        session.refresh(school)

        now = datetime.now(timezone.utc)
        v1 = SchoolContentVersion(
            school_id=school.id,
            summary="Published summary",
            status="published",
            published_at=now,
            published_by="author@example.com",
        )
        v2 = SchoolContentVersion(
            school_id=school.id,
            summary="Draft summary",
            status="draft",
        )

        session.add_all([v1, v2])
        session.commit()
        session.refresh(v1)
        session.refresh(v2)

        published = publish_school_version(
            session, school.id, v2.id, operator="editor@example.com"
        )
        session.commit()
        session.refresh(v1)
        session.refresh(v2)

        assert v1.status == "archived"
        assert v2.status == "published"
        assert v2.published_by == "editor@example.com"
        assert v2.published_at is not None
        assert published.id == v2.id
