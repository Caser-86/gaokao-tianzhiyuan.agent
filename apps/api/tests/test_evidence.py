from datetime import date

import pytest
from sqlmodel import Session

from app.services import evidence
from app.services.evidence import (
    UnknownEvidenceEntityError,
    build_evidence_package,
)


def _session_factory(engine):
    return lambda: Session(engine)


def test_build_school_evidence_package_returns_bounded_sql_items(seed_catalog, engine) -> None:
    seed_catalog(
        {
            "search_entry": {},
            "schools": [
                {
                    "slug": "demo-school",
                    "name": "演示大学",
                    "region": "江苏",
                    "city": "南京",
                    "summary": "用于测试的学校摘要。",
                    "sections": [
                        {
                            "type": "highlights",
                            "title": "学校亮点",
                            "items": ["拥有可追溯的演示资料。"],
                        }
                    ],
                    "ranking_references": [
                        {
                            "source": "演示榜单",
                            "year": 2025,
                            "label": "示例名次",
                            "scope": "综合",
                            "note": "仅用于测试。",
                            "url": "https://example.com/demo",
                        }
                    ],
                }
            ],
            "majors": [],
        }
    )

    items = build_evidence_package(
        entity_type="school",
        entity_slug="demo-school",
        session_factory=_session_factory(engine),
        max_items=10,
        max_chars=500,
    )

    assert [item.id for item in items] == [
        "school:demo-school:summary",
        "school:demo-school:section:0:0",
        "school:demo-school:ranking:1",
    ]
    assert items[0].source_name == "项目手工编写演示数据"
    assert items[0].source_url is None
    assert items[0].year is None
    assert items[0].province == "江苏"
    assert items[0].data_status == "demo"
    assert items[-1].source_name == "演示榜单"
    assert items[-1].source_url == "https://example.com/demo"
    assert all(item.text.strip() for item in items)
    assert len(items) <= 10
    assert sum(len(item.text) for item in items) <= 500

    assert (
        build_evidence_package(
            entity_type="school",
            entity_slug="演示大学",
            session_factory=_session_factory(engine),
            max_items=1,
        )[0].id
        == "school:demo-school:summary"
    )


def test_evidence_filters_by_major_region_and_exact_reference_year(seed_catalog, engine) -> None:
    seed_catalog(
        {
            "search_entry": {},
            "schools": [],
            "majors": [
                {
                    "slug": "demo-major",
                    "name": "演示专业",
                    "discipline": "工学",
                    "recommended_regions": ["江苏"],
                    "summary": "专业摘要。",
                    "sections": [],
                    "ranking_references": [
                        {
                            "source": "演示学科评估",
                            "year": 2023,
                            "label": "A-",
                            "scope": "一级学科",
                            "note": "演示引用。",
                            "url": "https://example.com/demo-major",
                        }
                    ],
                }
            ],
        }
    )

    items = build_evidence_package(
        entity_type="major",
        entity_slug="demo-major",
        province="江苏",
        year=2023,
        session_factory=_session_factory(engine),
    )
    assert [item.id for item in items] == ["major:demo-major:ranking:1"]
    assert items[0].year == 2023
    assert items[0].province is None

    assert (
        build_evidence_package(
            entity_type="major",
            entity_slug="demo-major",
            province="浙江",
            session_factory=_session_factory(engine),
        )
        == []
    )
    assert (
        build_evidence_package(
            entity_type="major",
            entity_slug="demo-major",
            year=2024,
            session_factory=_session_factory(engine),
        )
        == []
    )


def test_evidence_rejects_unknown_entity_and_oversized_item(seed_catalog, engine) -> None:
    seed_catalog(
        {
            "search_entry": {},
            "schools": [
                {
                    "slug": "demo-school",
                    "name": "演示大学",
                    "region": "江苏",
                    "city": "南京",
                    "summary": "这是一段超过预算的摘要。",
                    "sections": [],
                }
            ],
            "majors": [],
        }
    )

    with pytest.raises(UnknownEvidenceEntityError, match="unknown school"):
        build_evidence_package(
            entity_type="school",
            entity_slug="missing-school",
            session_factory=_session_factory(engine),
        )

    assert (
        build_evidence_package(
            entity_type="school",
            entity_slug="demo-school",
            session_factory=_session_factory(engine),
            max_chars=3,
        )
        == []
    )


def test_stale_provenance_is_not_returned_as_usable_evidence(
    seed_catalog, engine, monkeypatch
) -> None:
    seed_catalog(
        {
            "search_entry": {},
            "schools": [
                {
                    "slug": "demo-school",
                    "name": "演示大学",
                    "region": "江苏",
                    "city": "南京",
                    "summary": "摘要。",
                    "sections": [],
                }
            ],
            "majors": [],
        }
    )
    monkeypatch.setattr(
        evidence,
        "get_data_provenance",
        lambda: {
            "status": "demo",
            "source_name": "旧演示数据",
            "source_url": None,
            "updated_at": "2020-01-01",
            "applicable_year": None,
            "region": "江苏",
            "official": False,
            "disclaimer": "仅用于测试。",
        },
    )

    items = build_evidence_package(
        entity_type="school",
        entity_slug="demo-school",
        session_factory=_session_factory(engine),
        as_of=date(2026, 9, 15),
        max_age_days=30,
    )

    assert items == []
