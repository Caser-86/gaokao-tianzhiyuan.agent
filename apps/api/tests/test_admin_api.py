import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models.ingestion import ReviewQueue
from app.services import featured_content as featured_content_service


@pytest.fixture
def admin_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client, engine

    app.dependency_overrides.clear()


@pytest.fixture
def featured_content_file(tmp_path, monkeypatch):
    path = tmp_path / "featured-content.json"
    path.write_text(
        json.dumps(
            {
                "schools": [
                    {
                        "slug": "southeast-university",
                        "is_featured": True,
                        "hero_image_url": "",
                    },
                    {
                        "slug": "west-china-medical-center",
                        "is_featured": True,
                        "hero_image_url": "",
                    },
                ],
                "majors": [
                    {
                        "slug": "clinical-medicine",
                        "is_featured": True,
                    },
                    {
                        "slug": "computer-science",
                        "is_featured": True,
                    },
                ],
                "rotation": {
                    "schools": {
                        "enabled": True,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [
                            "southeast-university",
                            "west-china-medical-center",
                        ],
                    },
                    "majors": {
                        "enabled": True,
                        "frequency_days": 1,
                        "window_size": 1,
                        "ordered_slugs": [
                            "clinical-medicine",
                            "computer-science",
                        ],
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(featured_content_service, "FEATURED_CONTENT_PATH", path)
    return path


def test_review_queue_endpoint_requires_admin_header() -> None:
    with TestClient(app) as client:
        response = client.get("/api/admin/review-queue")

    assert response.status_code == 401
    assert response.json() == {"detail": "admin authentication required"}


def test_review_queue_endpoint_returns_pending_items_for_valid_admin_token(
    admin_client,
) -> None:
    client, engine = admin_client
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        session.add(
            ReviewQueue(
                entity_type="school",
                entity_id=101,
                candidate_version=2,
                diff_summary=["summary"],
                priority="normal",
                review_status="pending_review",
                created_at=now,
            )
        )
        session.add(
            ReviewQueue(
                entity_type="school",
                entity_id=102,
                candidate_version=3,
                diff_summary=["strengths"],
                priority="high",
                review_status="approved",
                created_at=now + timedelta(minutes=1),
            )
        )
        session.add(
            ReviewQueue(
                entity_type="major",
                entity_id=103,
                candidate_version=4,
                diff_summary=["risks"],
                priority="low",
                review_status="pending_review",
                created_at=now + timedelta(minutes=2),
            )
        )
        session.commit()

    response = client.get(
        "/api/admin/review-queue",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 1,
                "entity_type": "school",
                "entity_id": 101,
                "candidate_version": 2,
                "diff_summary": ["summary"],
                "priority": "normal",
                "review_status": "pending_review",
                "reviewed_by": None,
                "reviewed_at": None,
                "review_note": None,
                "created_at": now.isoformat().replace("+00:00", "Z"),
            },
            {
                "id": 3,
                "entity_type": "major",
                "entity_id": 103,
                "candidate_version": 4,
                "diff_summary": ["risks"],
                "priority": "low",
                "review_status": "pending_review",
                "reviewed_by": None,
                "reviewed_at": None,
                "review_note": None,
                "created_at": (now + timedelta(minutes=2)).isoformat().replace("+00:00", "Z"),
            },
        ]
    }


def test_review_queue_endpoint_uses_configured_admin_token(admin_client) -> None:
    client, _engine = admin_client
    previous_token = getattr(settings, "admin_token", "dev-admin-token")
    settings.admin_token = "task4-custom-token"
    try:
        response = client.get(
            "/api/admin/review-queue",
            headers={"x-admin-token": "task4-custom-token"},
        )
        assert response.status_code == 200
        assert response.json() == {"items": []}
    finally:
        settings.admin_token = previous_token


def test_featured_content_endpoint_returns_school_and_major_configuration(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    payload = response.json()
    assert {
        "slug": "southeast-university",
        "name": "东南大学",
        "is_featured": True,
        "hero_image_url": "",
    } in payload["schools"]
    assert {
        "slug": "west-china-medical-center",
        "name": "华西医学中心",
        "is_featured": True,
        "hero_image_url": "",
    } in payload["schools"]
    assert {
        "slug": "clinical-medicine",
        "name": "临床医学",
        "is_featured": True,
    } in payload["majors"]
    assert {
        "slug": "computer-science",
        "name": "计算机科学与技术",
        "is_featured": True,
    } in payload["majors"]


    assert payload["rotation"] == {
        "schools": {
            "enabled": True,
            "frequency_days": 1,
            "window_size": 1,
            "ordered_slugs": [
                "southeast-university",
                "west-china-medical-center",
            ],
        },
        "majors": {
            "enabled": True,
            "frequency_days": 1,
            "window_size": 1,
            "ordered_slugs": [
                "clinical-medicine",
                "computer-science",
            ],
        },
    }


def test_featured_content_endpoint_returns_today_preview(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["preview"] == {
        "schools": [
            {
                "slug": "southeast-university",
                "name": "东南大学",
            }
        ],
        "majors": [
            {
                "slug": "clinical-medicine",
                "name": "临床医学",
            }
        ],
    }


def test_update_featured_school_persists_is_featured_and_image_url(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/schools/southeast-university",
        headers={"x-admin-token": settings.admin_token},
        json={
            "is_featured": False,
            "hero_image_url": "https://cdn.example.com/southeast.jpg",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "东南大学",
        "is_featured": False,
        "hero_image_url": "https://cdn.example.com/southeast.jpg",
    }
    saved = json.loads(featured_content_file.read_text(encoding="utf-8"))
    assert saved["schools"][0] == {
        "slug": "southeast-university",
        "is_featured": False,
        "hero_image_url": "https://cdn.example.com/southeast.jpg",
    }


def test_update_featured_major_rejects_unknown_slug(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/majors/missing-major",
        headers={"x-admin-token": settings.admin_token},
        json={"is_featured": True},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "featured content entity not found"}


def test_update_school_rotation_rule_persists_configuration(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/rotation/schools",
        headers={"x-admin-token": settings.admin_token},
        json={
            "enabled": True,
            "frequency_days": 2,
            "window_size": 2,
            "ordered_slugs": [
                "west-china-medical-center",
                "southeast-university",
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "frequency_days": 2,
        "window_size": 2,
        "ordered_slugs": [
            "west-china-medical-center",
            "southeast-university",
        ],
    }

    saved = json.loads(featured_content_file.read_text(encoding="utf-8"))
    assert saved["rotation"]["schools"] == {
        "enabled": True,
        "frequency_days": 2,
        "window_size": 2,
        "ordered_slugs": [
            "west-china-medical-center",
            "southeast-university",
        ],
    }


def test_update_major_rotation_rule_rejects_unknown_slug(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/rotation/majors",
        headers={"x-admin-token": settings.admin_token},
        json={
            "enabled": True,
            "frequency_days": 1,
            "window_size": 1,
            "ordered_slugs": ["missing-major"],
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "featured rotation slug not found"}


def test_approve_review_queue_item_updates_status_and_audit_fields(admin_client) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        queue_item = ReviewQueue(
            entity_type="school",
            entity_id=201,
            candidate_version=5,
            diff_summary=["summary"],
            priority="normal",
            review_status="pending_review",
        )
        session.add(queue_item)
        session.commit()
        session.refresh(queue_item)
        queue_id = queue_item.id

    response = client.post(
        f"/api/admin/review-queue/{queue_id}/approve",
        headers={"x-admin-token": settings.admin_token},
        json={"reviewed_by": "editor@example.com"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "approved"
    assert body["reviewed_by"] == "editor@example.com"
    assert body["reviewed_at"] is not None
    assert body["review_note"] is None

    with Session(engine) as session:
        stored = session.get(ReviewQueue, queue_id)
        assert stored is not None
        assert stored.review_status == "approved"
        assert stored.reviewed_by == "editor@example.com"
        assert stored.reviewed_at is not None
        assert stored.review_note is None


def test_reject_review_queue_item_updates_status_and_note(admin_client) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        queue_item = ReviewQueue(
            entity_type="major",
            entity_id=301,
            candidate_version=6,
            diff_summary=["risks"],
            priority="high",
            review_status="pending_review",
        )
        session.add(queue_item)
        session.commit()
        session.refresh(queue_item)
        queue_id = queue_item.id

    response = client.post(
        f"/api/admin/review-queue/{queue_id}/reject",
        headers={"x-admin-token": settings.admin_token},
        json={
            "reviewed_by": "reviewer@example.com",
            "review_note": "source data is stale",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "rejected"
    assert body["reviewed_by"] == "reviewer@example.com"
    assert body["reviewed_at"] is not None
    assert body["review_note"] == "source data is stale"

    with Session(engine) as session:
        stored = session.get(ReviewQueue, queue_id)
        assert stored is not None
        assert stored.review_status == "rejected"
        assert stored.reviewed_by == "reviewer@example.com"
        assert stored.reviewed_at is not None
        assert stored.review_note == "source data is stale"


def test_review_action_returns_404_for_unknown_queue_id(admin_client) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/review-queue/999/approve",
        headers={"x-admin-token": settings.admin_token},
        json={"reviewed_by": "editor@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "review queue item not found"}


def test_review_action_returns_409_for_non_pending_item(admin_client) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        queue_item = ReviewQueue(
            entity_type="school",
            entity_id=401,
            candidate_version=7,
            diff_summary=["summary"],
            priority="normal",
            review_status="approved",
            reviewed_by="editor@example.com",
            reviewed_at=datetime.now(timezone.utc),
        )
        session.add(queue_item)
        session.commit()
        session.refresh(queue_item)
        queue_id = queue_item.id

    response = client.post(
        f"/api/admin/review-queue/{queue_id}/reject",
        headers={"x-admin-token": settings.admin_token},
        json={"reviewed_by": "reviewer@example.com"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "review queue item is already finalized"}


def test_review_action_requires_admin_header(admin_client) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        queue_item = ReviewQueue(
            entity_type="school",
            entity_id=501,
            candidate_version=8,
            diff_summary=["summary"],
            priority="normal",
            review_status="pending_review",
        )
        session.add(queue_item)
        session.commit()
        session.refresh(queue_item)
        queue_id = queue_item.id

    response = client.post(
        f"/api/admin/review-queue/{queue_id}/approve",
        json={"reviewed_by": "editor@example.com"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "admin authentication required"}
