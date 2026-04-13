# Admin Review API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a database-backed admin review queue API that returns pending items and supports approve and reject actions with minimal audit metadata.

**Architecture:** Extend the existing `ReviewQueue` SQLModel table and keep review workflow logic inside the admin API boundary. Add a reusable database session dependency, return real queue rows from `GET /api/admin/review-queue`, then add `approve` and `reject` endpoints that enforce valid state transitions and persist reviewer metadata without touching publishing logic.

**Tech Stack:** FastAPI, SQLModel, SQLite for tests, pytest, httpx/TestClient

---

### Task 1: Back The Admin Review Queue With The Database

**Files:**
- Modify: `apps/api/app/config.py`
- Modify: `apps/api/app/db.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/routers/admin.py`
- Modify: `apps/api/tests/test_admin_api.py`
- Test: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing test**

Replace `apps/api/tests/test_admin_api.py` with:

```python
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models.ingestion import ReviewQueue


@pytest.fixture
def admin_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
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
                "created_at": now.isoformat(),
            },
            {
                "id": 3,
                "entity_type": "major",
                "entity_id": 103,
                "candidate_version": 4,
                "diff_summary": ["risks"],
                "priority": "low",
                "review_status": "pending_review",
                "created_at": (now + timedelta(minutes=2)).isoformat(),
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_admin_api.py::test_review_queue_endpoint_returns_pending_items_for_valid_admin_token -v`

Expected: `FAIL` because `app.db.get_session` does not exist yet or the endpoint still returns `{"items": []}` instead of database rows.

- [ ] **Step 3: Write minimal implementation**

Update `apps/api/app/config.py` to add a default database URL:

```python
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ADMIN_TOKEN = "dev-admin-token"
SAFE_DEFAULT_ADMIN_TOKEN_ENVIRONMENTS = {"development", "test"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAOKAO_AGENT_")

    app_name: str = "gaokao-agent-api"
    api_prefix: str = "/api"
    environment: str = "development"
    admin_token: str = DEFAULT_ADMIN_TOKEN
    database_url: str = "sqlite:///./gaokao-agent.db"

    @model_validator(mode="after")
    def validate_admin_token(self) -> "Settings":
        environment = self.environment.strip().lower()
        if (
            self.admin_token == DEFAULT_ADMIN_TOKEN
            and environment not in SAFE_DEFAULT_ADMIN_TOKEN_ENVIRONMENTS
        ):
            raise ValueError(
                "default admin token is only allowed in development/test mode"
            )
        return self


settings = Settings()
```

Update `apps/api/app/db.py` to expose a reusable session dependency:

```python
from collections.abc import Generator
from functools import lru_cache

from sqlmodel import SQLModel, Session, create_engine

from .config import settings


@lru_cache
def get_engine(url: str | None = None):
    engine_url = url or settings.database_url
    connect_args = {"check_same_thread": False} if engine_url.startswith("sqlite") else {}
    return create_engine(engine_url, future=True, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def create_all_models(engine=None) -> None:
    SQLModel.metadata.create_all(engine or get_engine())
```

Update `apps/api/app/main.py` so local startup creates tables:

```python
from fastapi import FastAPI

from .config import settings
from .db import create_all_models
from .routers.admin import router as admin_router
from .routers.platform import router as platform_router
from .routers.public import router as public_router


app = FastAPI(title=settings.app_name)
app.include_router(admin_router)
app.include_router(platform_router)
app.include_router(public_router)


@app.on_event("startup")
def on_startup() -> None:
    create_all_models()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

Update `apps/api/app/routers/admin.py` to query real pending rows:

```python
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import SQLModel, Session, select

from ..config import settings
from ..db import get_session
from ..models.ingestion import ReviewQueue

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ReviewQueueItemResponse(SQLModel):
    id: int
    entity_type: str
    entity_id: int
    candidate_version: int | None = None
    diff_summary: list[str]
    priority: str
    review_status: str
    created_at: datetime


class ReviewQueueListResponse(SQLModel):
    items: list[ReviewQueueItemResponse]


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin authentication required",
        )


@router.get("/review-queue", response_model=ReviewQueueListResponse)
def list_review_queue(
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ReviewQueueListResponse:
    stmt = (
        select(ReviewQueue)
        .where(ReviewQueue.review_status == "pending_review")
        .order_by(ReviewQueue.created_at)
    )
    items = session.exec(stmt).all()
    return ReviewQueueListResponse(
        items=[ReviewQueueItemResponse.model_validate(item) for item in items]
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_admin_api.py -v`

Expected: `PASS` with 3 passing admin API tests.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/config.py apps/api/app/db.py apps/api/app/main.py apps/api/app/routers/admin.py apps/api/tests/test_admin_api.py
git commit -m "feat(api): back admin review queue with database"
```

### Task 2: Add Review Decision Actions And Audit Metadata

**Files:**
- Modify: `apps/api/app/models/ingestion.py`
- Modify: `apps/api/app/routers/admin.py`
- Modify: `apps/api/tests/test_admin_api.py`
- Test: `apps/api/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing test**

Replace `apps/api/tests/test_admin_api.py` with:

```python
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.config import settings
from app.db import get_session
from app.main import app
from app.models.ingestion import ReviewQueue


@pytest.fixture
def admin_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
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
                "created_at": now.isoformat(),
            },
            {
                "id": 3,
                "entity_type": "major",
                "entity_id": 103,
                "candidate_version": 4,
                "diff_summary": ["risks"],
                "priority": "low",
                "review_status": "pending_review",
                "created_at": (now + timedelta(minutes=2)).isoformat(),
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_admin_api.py::test_approve_review_queue_item_updates_status_and_audit_fields -v`

Expected: `FAIL` because `ReviewQueue` does not have the audit fields yet and the approve endpoint does not exist.

- [ ] **Step 3: Write minimal implementation**

Update `apps/api/app/models/ingestion.py` to store audit metadata:

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ReviewQueue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(..., nullable=False)
    entity_id: int = Field(..., nullable=False, index=True)
    candidate_version: Optional[int] = Field(default=None, nullable=True)
    diff_summary: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    priority: str = Field(default="normal", nullable=False, index=False)
    review_status: str = Field(default="pending_review", nullable=False)
    reviewed_by: Optional[str] = Field(default=None, nullable=True)
    reviewed_at: Optional[datetime] = Field(default=None, nullable=True)
    review_note: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
```

Update `apps/api/app/routers/admin.py` to add request models and decision endpoints:

```python
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import SQLModel, Session, select

from ..config import settings
from ..db import get_session
from ..models.ingestion import ReviewQueue

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ReviewQueueItemResponse(SQLModel):
    id: int
    entity_type: str
    entity_id: int
    candidate_version: int | None = None
    diff_summary: list[str]
    priority: str
    review_status: str
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    created_at: datetime


class ReviewQueueListResponse(SQLModel):
    items: list[ReviewQueueItemResponse]


class ReviewDecisionRequest(SQLModel):
    reviewed_by: str
    review_note: str | None = None


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin authentication required",
        )


def serialize_review_queue_item(item: ReviewQueue) -> ReviewQueueItemResponse:
    return ReviewQueueItemResponse.model_validate(item)


def get_review_queue_item(session: Session, queue_id: int) -> ReviewQueue:
    queue_item = session.get(ReviewQueue, queue_id)
    if queue_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="review queue item not found",
        )
    return queue_item


def finalize_review_queue_item(
    queue_item: ReviewQueue,
    decision: str,
    payload: ReviewDecisionRequest,
) -> ReviewQueue:
    if queue_item.review_status != "pending_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="review queue item is already finalized",
        )

    queue_item.review_status = decision
    queue_item.reviewed_by = payload.reviewed_by
    queue_item.reviewed_at = datetime.now(timezone.utc)
    queue_item.review_note = payload.review_note
    return queue_item


@router.get("/review-queue", response_model=ReviewQueueListResponse)
def list_review_queue(
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ReviewQueueListResponse:
    stmt = (
        select(ReviewQueue)
        .where(ReviewQueue.review_status == "pending_review")
        .order_by(ReviewQueue.created_at)
    )
    items = session.exec(stmt).all()
    return ReviewQueueListResponse(
        items=[serialize_review_queue_item(item) for item in items]
    )


@router.post("/review-queue/{queue_id}/approve", response_model=ReviewQueueItemResponse)
def approve_review_queue_item(
    queue_id: int,
    payload: ReviewDecisionRequest,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ReviewQueueItemResponse:
    queue_item = get_review_queue_item(session, queue_id)
    queue_item = finalize_review_queue_item(queue_item, "approved", payload)
    session.add(queue_item)
    session.commit()
    session.refresh(queue_item)
    return serialize_review_queue_item(queue_item)


@router.post("/review-queue/{queue_id}/reject", response_model=ReviewQueueItemResponse)
def reject_review_queue_item(
    queue_id: int,
    payload: ReviewDecisionRequest,
    _authorized: None = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ReviewQueueItemResponse:
    queue_item = get_review_queue_item(session, queue_id)
    queue_item = finalize_review_queue_item(queue_item, "rejected", payload)
    session.add(queue_item)
    session.commit()
    session.refresh(queue_item)
    return serialize_review_queue_item(queue_item)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_admin_api.py -v`

Expected: `PASS` with 8 passing admin API tests.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/models/ingestion.py apps/api/app/routers/admin.py apps/api/tests/test_admin_api.py
git commit -m "feat(api): add admin review decision actions"
```
