import json
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models.ingestion import MediaAnalysisEvent, ReviewQueue
from app.routers import admin as admin_router_module
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
    expected_preview = featured_content_service.build_featured_content_preview()

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["preview"]["today"] == expected_preview["today"]


def test_featured_content_endpoint_returns_seven_day_schedule(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client
    today = date.today()
    expected_preview = featured_content_service.build_featured_content_preview()

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    schedule = response.json()["preview"]["schedule"]

    assert len(schedule) == 7
    assert schedule[0]["date"] == today.isoformat()
    assert schedule[0]["schools"] == expected_preview["schedule"][0]["schools"]
    assert schedule[0]["majors"] == expected_preview["schedule"][0]["majors"]
    assert schedule[1]["date"] == (today + timedelta(days=1)).isoformat()
    assert schedule[1]["schools"] == expected_preview["schedule"][1]["schools"]
    assert schedule[1]["majors"] == expected_preview["schedule"][1]["majors"]


def test_featured_content_endpoint_returns_next_preview(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client
    expected_preview = featured_content_service.build_featured_content_preview()

    response = client.get(
        "/api/admin/featured-content",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["preview"]["next"] == expected_preview["next"]


def test_featured_content_endpoint_returns_selected_date_preview(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content?preview_date=2026-04-15",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["preview"]["selected_date"] == {
        "date": "2026-04-15",
        "weekday": "周三",
        "schools": [
            {
                "slug": "west-china-medical-center",
                "name": "华西医学中心",
            }
        ],
        "majors": [
            {
                "slug": "computer-science",
                "name": "计算机科学与技术",
            }
        ],
    }
    assert response.json()["preview"]["selected_date_error"] is None


def test_featured_content_endpoint_returns_local_error_for_invalid_preview_date(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/featured-content?preview_date=2026-99-99",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["preview"]["selected_date"] is None
    assert response.json()["preview"]["selected_date_error"] == "预览日期格式无效"


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


def test_suggest_featured_school_image_returns_candidate(
    admin_client,
    featured_content_file,
    monkeypatch,
) -> None:
    client, _engine = admin_client

    monkeypatch.setattr(
        featured_content_service,
        "fetch_school_image_candidate",
        lambda slug: {
            "slug": slug,
            "name": "东南大学",
            "status": "found",
            "source_url": "https://www.seu.edu.cn/",
            "suggested_image_url": "https://www.seu.edu.cn/assets/hero.jpg",
            "message": None,
        },
    )

    response = client.post(
        "/api/admin/featured-content/schools/southeast-university/suggest-image",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "slug": "southeast-university",
        "name": "东南大学",
        "status": "found",
        "source_url": "https://www.seu.edu.cn/",
        "suggested_image_url": "https://www.seu.edu.cn/assets/hero.jpg",
        "message": None,
    }


def test_suggest_featured_school_image_returns_missing_when_school_has_no_website(
    admin_client,
    featured_content_file,
    monkeypatch,
) -> None:
    client, _engine = admin_client

    monkeypatch.setattr(
        featured_content_service,
        "fetch_school_image_candidate",
        lambda slug: {
            "slug": slug,
            "name": "东南大学",
            "status": "missing",
            "source_url": None,
            "suggested_image_url": None,
            "message": "学校未配置可抓取的官网地址",
        },
    )

    response = client.post(
        "/api/admin/featured-content/schools/southeast-university/suggest-image",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "missing"
    assert response.json()["message"] == "学校未配置可抓取的官网地址"


def test_suggest_featured_school_image_returns_404_for_unknown_slug(
    admin_client,
    featured_content_file,
) -> None:
    client, _engine = admin_client

    response = client.post(
        "/api/admin/featured-content/schools/missing-school/suggest-image",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "featured content entity not found"}


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


def test_smart_analysis_settings_endpoint_returns_bootstrap_default(admin_client) -> None:
    client, _engine = admin_client

    response = client.get(
        "/api/admin/smart-analysis/settings",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {"mode": settings.smart_analysis_mode}


def test_update_smart_analysis_settings_persists_mode(admin_client) -> None:
    client, _engine = admin_client

    response = client.put(
        "/api/admin/smart-analysis/settings",
        headers={"x-admin-token": settings.admin_token},
        json={"mode": "gated"},
    )

    assert response.status_code == 200
    assert response.json() == {"mode": "gated"}


def test_media_analysis_events_endpoint_returns_recent_items_for_valid_admin_token(
    admin_client,
) -> None:
    client, engine = admin_client
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-older",
                message_id="msg-older",
                media_id="media-older",
                media_type="image",
                provider="pending",
                status="pending",
                summary="older summary",
                rendered_reply="",
                extracted_fields={"province": "河南"},
                context={
                    "msg_type": "image",
                    "pic_url": "https://example.com/older.png",
                },
                auto_routed_to_chat=False,
                created_at=now,
            )
        )
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account_image_media_analysis",
                user_id="wx-openid-newer",
                message_id="msg-newer",
                media_id="media-newer",
                media_type="image",
                provider="openai_compatible",
                status="success",
                summary="识别到河南560分理科，目标专业计算机科学与技术",
                rendered_reply="图片已进入高考分析链路",
                extracted_fields={
                    "province": "河南",
                    "score": 560,
                    "subject": "理科",
                },
                context={
                    "msg_type": "image",
                    "pic_url": "https://example.com/newer.png",
                    "create_time": "1710000001",
                },
                auto_routed_to_chat=True,
                created_at=now + timedelta(minutes=1),
            )
        )
        session.commit()

    response = client.get(
        "/api/admin/media-analysis-events?limit=1",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 2,
                "channel": "wechat",
                "source": "wechat_official_account_image_media_analysis",
                "user_id": "wx-openid-newer",
                "message_id": "msg-newer",
                "media_id": "media-newer",
                "media_type": "image",
                "provider": "openai_compatible",
                "status": "success",
                "summary": "识别到河南560分理科，目标专业计算机科学与技术",
                "rendered_reply": "图片已进入高考分析链路",
                "extracted_fields": {
                    "province": "河南",
                    "score": 560,
                    "subject": "理科",
                },
                "context": {
                    "msg_type": "image",
                    "pic_url": "https://example.com/newer.png",
                    "create_time": "1710000001",
                },
                "retryable": True,
                "retry_block_reason": None,
                "auto_routed_to_chat": True,
                "created_at": (now + timedelta(minutes=1))
                .isoformat()
                .replace("+00:00", "Z"),
            }
        ]
    }


def test_media_analysis_events_endpoint_supports_status_user_and_auto_route_filters(
    admin_client,
) -> None:
    client, engine = admin_client
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-1",
                message_id="msg-1",
                media_id="media-1",
                media_type="image",
                provider="openai_compatible",
                status="success",
                summary="match me",
                rendered_reply="reply-1",
                extracted_fields={"province": "河南"},
                context={
                    "msg_type": "image",
                    "pic_url": "https://example.com/1.png",
                },
                auto_routed_to_chat=True,
                created_at=now,
            )
        )
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-1",
                message_id="msg-2",
                media_id="media-2",
                media_type="image",
                provider="openai_compatible",
                status="pending",
                summary="wrong status",
                rendered_reply="reply-2",
                extracted_fields={},
                context={"msg_type": "image"},
                auto_routed_to_chat=True,
                created_at=now + timedelta(minutes=1),
            )
        )
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-2",
                message_id="msg-3",
                media_id="media-3",
                media_type="image",
                provider="openai_compatible",
                status="success",
                summary="wrong user",
                rendered_reply="reply-3",
                extracted_fields={},
                context={"msg_type": "image"},
                auto_routed_to_chat=True,
                created_at=now + timedelta(minutes=2),
            )
        )
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-1",
                message_id="msg-4",
                media_id="media-4",
                media_type="image",
                provider="openai_compatible",
                status="success",
                summary="wrong routing",
                rendered_reply="reply-4",
                extracted_fields={},
                context={"msg_type": "image"},
                auto_routed_to_chat=False,
                created_at=now + timedelta(minutes=3),
            )
        )
        session.commit()

    response = client.get(
        "/api/admin/media-analysis-events?status=success&user_id=wx-openid-1&auto_routed_to_chat=1",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "channel": "wechat",
            "source": "wechat_official_account",
            "user_id": "wx-openid-1",
            "message_id": "msg-1",
            "media_id": "media-1",
            "media_type": "image",
            "provider": "openai_compatible",
            "status": "success",
            "summary": "match me",
            "rendered_reply": "reply-1",
            "extracted_fields": {"province": "河南"},
            "context": {
                "msg_type": "image",
                "pic_url": "https://example.com/1.png",
            },
            "retryable": True,
            "retry_block_reason": None,
            "auto_routed_to_chat": True,
            "created_at": now.isoformat().replace("+00:00", "Z"),
        }
    ]


def test_media_analysis_events_endpoint_reports_blocked_retry_reason_for_video_records(
    admin_client,
) -> None:
    client, engine = admin_client
    now = datetime.now(timezone.utc)

    with Session(engine) as session:
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account_video_media_analysis",
                user_id="wx-openid-video",
                message_id="msg-video",
                media_id="media-video",
                media_type="video",
                provider="openai_compatible",
                status="failed",
                summary="video unsupported",
                rendered_reply="reply-video",
                extracted_fields={},
                context={
                    "msg_type": "video",
                    "media_id": "media-video",
                    "failure_reason": "video unsupported",
                },
                auto_routed_to_chat=False,
                created_at=now,
            )
        )
        session.commit()

    response = client.get(
        "/api/admin/media-analysis-events?status=failed",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": 1,
            "channel": "wechat",
            "source": "wechat_official_account_video_media_analysis",
            "user_id": "wx-openid-video",
            "message_id": "msg-video",
            "media_id": "media-video",
            "media_type": "video",
            "provider": "openai_compatible",
            "status": "failed",
            "summary": "video unsupported",
            "rendered_reply": "reply-video",
            "extracted_fields": {},
            "context": {
                "msg_type": "video",
                "media_id": "media-video",
                "failure_reason": "video unsupported",
            },
            "retryable": False,
            "retry_block_reason": "\u975e\u56fe\u7247\u5a92\u4f53\u8bb0\u5f55\u6682\u4e0d\u652f\u6301\u624b\u52a8\u91cd\u8bd5",
            "auto_routed_to_chat": False,
            "created_at": now.isoformat().replace("+00:00", "Z"),
        }
    ]


def test_retry_media_analysis_endpoint_creates_new_retry_record(
    admin_client,
    monkeypatch,
) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-retry",
                message_id="msg-retry-1",
                media_id="media-retry-1",
                media_type="image",
                provider="openai_compatible",
                status="success",
                summary="original summary",
                rendered_reply="original reply",
                extracted_fields={"province": "河南", "score": 560},
                context={
                    "to_user_name": "gh_retry",
                    "from_user_name": "wx-openid-retry",
                    "create_time": "1710000001",
                    "msg_type": "image",
                    "msg_id": "msg-retry-1",
                    "media_id": "media-retry-1",
                    "pic_url": "https://example.com/retry-image.png",
                },
                auto_routed_to_chat=False,
            )
        )
        session.commit()

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            assert request.media_type == "image"
            assert request.user_id == "wx-openid-retry"
            assert request.payload["PicUrl"] == "https://example.com/retry-image.png"
            return admin_router_module.MediaAnalysisResult(
                status="success",
                provider="retry-provider",
                summary="retried summary",
                rendered_reply="retried reply",
                extracted_fields={"province": "河南", "score": 565},
            )

    monkeypatch.setattr(
        admin_router_module,
        "media_analysis_provider",
        FakeMediaAnalysisProvider(),
    )

    response = client.post(
        "/api/admin/media-analysis-events/1/retry",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "channel": "wechat",
        "source": "admin_media_analysis_retry",
        "user_id": "wx-openid-retry",
        "message_id": "msg-retry-1",
        "media_id": "media-retry-1",
        "media_type": "image",
        "provider": "retry-provider",
        "status": "success",
        "summary": "retried summary",
        "rendered_reply": "retried reply",
        "extracted_fields": {"province": "河南", "score": 565},
        "context": {
            "to_user_name": "gh_retry",
            "from_user_name": "wx-openid-retry",
            "create_time": "1710000001",
            "msg_type": "image",
            "msg_id": "msg-retry-1",
            "media_id": "media-retry-1",
            "pic_url": "https://example.com/retry-image.png",
            "retried_from_event_id": 1,
            "retry_trigger": "admin_manual",
        },
        "retryable": True,
        "retry_block_reason": None,
        "auto_routed_to_chat": False,
        "created_at": response.json()["created_at"],
    }


def test_retry_media_analysis_endpoint_rejects_image_records_without_pic_url(
    admin_client,
) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-no-pic",
                message_id="msg-no-pic",
                media_id="media-no-pic",
                media_type="image",
                provider="openai_compatible",
                status="success",
                summary="summary",
                rendered_reply="reply",
                extracted_fields={},
                context={"msg_type": "image"},
                auto_routed_to_chat=False,
            )
        )
        session.commit()

    response = client.post(
        "/api/admin/media-analysis-events/1/retry",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "图片记录缺少 pic_url，暂不支持手动重试"
    }


def test_retry_media_analysis_endpoint_rejects_non_image_records(
    admin_client,
) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account_video_media_analysis",
                user_id="wx-openid-video-blocked",
                message_id="msg-video-blocked",
                media_id="media-video-blocked",
                media_type="video",
                provider="openai_compatible",
                status="failed",
                summary="video unsupported",
                rendered_reply="reply",
                extracted_fields={},
                context={"msg_type": "video", "media_id": "media-video-blocked"},
                auto_routed_to_chat=False,
            )
        )
        session.commit()

    response = client.post(
        "/api/admin/media-analysis-events/1/retry",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "非图片媒体记录暂不支持手动重试"
    }


def test_retry_media_analysis_endpoint_persists_failure_reason(
    admin_client,
    monkeypatch,
) -> None:
    client, engine = admin_client

    with Session(engine) as session:
        session.add(
            MediaAnalysisEvent(
                channel="wechat",
                source="wechat_official_account",
                user_id="wx-openid-retry-failed",
                message_id="msg-retry-failed-1",
                media_id="media-retry-failed-1",
                media_type="image",
                provider="openai_compatible",
                status="success",
                summary="original summary",
                rendered_reply="original reply",
                extracted_fields={},
                context={
                    "to_user_name": "gh_retry_failed",
                    "from_user_name": "wx-openid-retry-failed",
                    "create_time": "1710000001",
                    "msg_type": "image",
                    "msg_id": "msg-retry-failed-1",
                    "media_id": "media-retry-failed-1",
                    "pic_url": "https://example.com/retry-failed-image.png",
                },
                auto_routed_to_chat=False,
            )
        )
        session.commit()

    class FakeMediaAnalysisProvider:
        def analyze(self, *, request):
            assert request.media_type == "image"
            assert request.user_id == "wx-openid-retry-failed"
            return admin_router_module.MediaAnalysisResult(
                status="failed",
                provider="retry-provider",
                failure_reason="上游媒体分析请求失败：HTTP 429",
            )

    monkeypatch.setattr(
        admin_router_module,
        "media_analysis_provider",
        FakeMediaAnalysisProvider(),
    )

    response = client.post(
        "/api/admin/media-analysis-events/1/retry",
        headers={"x-admin-token": settings.admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "channel": "wechat",
        "source": "admin_media_analysis_retry",
        "user_id": "wx-openid-retry-failed",
        "message_id": "msg-retry-failed-1",
        "media_id": "media-retry-failed-1",
        "media_type": "image",
        "provider": "retry-provider",
        "status": "failed",
        "summary": "",
        "rendered_reply": "",
        "extracted_fields": {},
        "context": {
            "to_user_name": "gh_retry_failed",
            "from_user_name": "wx-openid-retry-failed",
            "create_time": "1710000001",
            "msg_type": "image",
            "msg_id": "msg-retry-failed-1",
            "media_id": "media-retry-failed-1",
            "pic_url": "https://example.com/retry-failed-image.png",
            "retried_from_event_id": 1,
            "retry_trigger": "admin_manual",
            "failure_reason": "上游媒体分析请求失败：HTTP 429",
        },
        "retryable": True,
        "retry_block_reason": None,
        "auto_routed_to_chat": False,
        "created_at": response.json()["created_at"],
    }


def test_smart_analysis_user_entitlement_can_be_granted_and_revoked(admin_client) -> None:
    client, _engine = admin_client

    grant_response = client.put(
        "/api/admin/smart-analysis/users/wx-openid-123",
        headers={"x-admin-token": settings.admin_token},
        json={"smart_analysis_enabled": True},
    )

    assert grant_response.status_code == 200
    assert grant_response.json() == {
        "user_id": "wx-openid-123",
        "entitlements": [{"name": "smart_analysis", "enabled": True}],
    }

    revoke_response = client.put(
        "/api/admin/smart-analysis/users/wx-openid-123",
        headers={"x-admin-token": settings.admin_token},
        json={"smart_analysis_enabled": False},
    )

    assert revoke_response.status_code == 200
    assert revoke_response.json() == {
        "user_id": "wx-openid-123",
        "entitlements": [],
    }
