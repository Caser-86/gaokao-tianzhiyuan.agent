from pathlib import Path

from sqlmodel import Session, select

from app.models.catalog import School
from app.scripts import seed_catalog


def test_seed_catalog_uses_repository_root_data_directory() -> None:
    expected_data_dir = Path(__file__).resolve().parents[3] / "data"

    assert expected_data_dir == seed_catalog.DATA_DIR


def test_seed_catalog_if_empty_does_not_overwrite_existing_catalog(
    engine,
    monkeypatch,
) -> None:
    existing_school = School(
        slug="edited-school",
        name="管理员编辑后的学校",
        region="江苏",
        city="南京",
        summary="管理员维护的内容",
    )
    with Session(engine) as session:
        session.add(existing_school)
        session.commit()

    monkeypatch.setattr(seed_catalog, "get_engine", lambda: engine)
    monkeypatch.setattr(
        seed_catalog,
        "load_catalog",
        lambda: (_ for _ in ()).throw(AssertionError("catalog should not be loaded")),
    )

    seed_catalog.seed_catalog(only_if_empty=True)

    with Session(engine) as session:
        school = session.exec(select(School).where(School.slug == "edited-school")).one()
        assert school.summary == "管理员维护的内容"
