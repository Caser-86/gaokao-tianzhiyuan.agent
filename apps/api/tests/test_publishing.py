from sqlmodel import Session, SQLModel, create_engine

from app.models.content import School, SchoolContentVersion
from app.services.publishing import publish_school_version


def test_publish_school_version_marks_only_target_version_published() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        school = School(name="示例大学", slug="example-university")
        session.add(school)
        session.commit()
        session.refresh(school)

        v1 = SchoolContentVersion(
            school_id=school.id,
            version=1,
            summary="old",
            status="published",
            published_by="author",
        )
        v2 = SchoolContentVersion(
            school_id=school.id,
            version=2,
            summary="new",
            status="draft",
        )

        session.add_all([v1, v2])
        session.commit()
        session.refresh(v1)
        session.refresh(v2)

        publish_school_version(session, school.id, v2.id, operator="editor@example.com")
        session.commit()
        session.refresh(v1)
        session.refresh(v2)

        assert v1.status == "archived"
        assert v2.status == "published"
        assert v2.published_by == "editor@example.com"
