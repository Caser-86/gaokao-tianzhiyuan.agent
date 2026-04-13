from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models.ingestion import ReviewQueue


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
