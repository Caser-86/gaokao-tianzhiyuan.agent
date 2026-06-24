import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.models.catalog import School
from app.models.content import SchoolContentVersion, VersionStatus


def test_school_version_must_be_unique_per_school_post_commit() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        school = School(
            name="Example University",
            slug="example-university-invariants",
            region="江苏",
            city="南京",
        )
        session.add(school)
        session.commit()
        session.refresh(school)
        school_id = school.id

        session.add(
            SchoolContentVersion(
                school_id=school_id,
                version=1,
                summary="v1",
                status=VersionStatus.draft,
            )
        )
        session.commit()

    with Session(engine) as session:
        session.add(
            SchoolContentVersion(
                school_id=school_id,
                version=1,
                summary="duplicate",
                status=VersionStatus.draft,
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()


def test_only_one_published_version_per_school_post_commit() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        school = School(
            name="Second Example University",
            slug="example-university-published",
            region="江苏",
            city="南京",
        )
        session.add(school)
        session.commit()
        session.refresh(school)
        school_id = school.id

        session.add(
            SchoolContentVersion(
                school_id=school_id,
                version=1,
                summary="published v1",
                status=VersionStatus.published,
            )
        )
        session.commit()

    with Session(engine) as session:
        session.add(
            SchoolContentVersion(
                school_id=school_id,
                version=2,
                summary="published v2",
                status=VersionStatus.published,
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()
