# Ingestion Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the ingestion review queue diff helper and persist its tracked fields so ingestion changes can be routed to reviewers.

**Architecture:** Track the review queue in a dedicated SQLModel table (AuditQueue) that stores entity metadata, assessed diff summary, and pending state. The service layer exposes a `build_review_candidate` helper that compares tracked fields (`summary`, `strengths`, `suitable_for`, and `risks`), builds the diff payload, and inserts pending entries.

**Tech Stack:** Python 3.11, FastAPI stack, SQLModel (SQLite for tests), Pytest.

---

### Task 1: Build ingestion review diff helper

**Files:**
- Create: `app/models/ingestion.py`
- Create: `app/services/ingestion.py`
- Create: `tests/test_ingestion.py`

- [ ] **Step 1: Write the failing test**

```python
from sqlmodel import Session, SQLModel, create_engine

from app.services.ingestion import build_review_candidate
from app.models.ingestion import ReviewQueue


def test_build_review_candidate_detects_tracked_field_changes():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    tracked_fields = {
        "summary": "old",
        "strengths": "former",
        "suitable_for": "none",
        "risks": "low",
    }
    candidate_payload = tracked_fields.copy()
    crawled_payload = tracked_fields.copy()
    crawled_payload["strengths"] = "new"

    with Session(engine) as session:
        candidate = build_review_candidate(
            session,
            entity_type="school_content_version",
            entity_id=1,
            current_payload=candidate_payload,
            crawled_payload=crawled_payload,
        )

        assert candidate["diff_summary"] == ["strengths"]
        assert candidate["has_changes"]
        assert candidate["status"] == "pending_review"
        assert candidate["entity_type"] == "school_content_version"
        assert candidate["entity_id"] == 1
        assert session.exec(ReviewQueue.select()).one().status == "pending_review"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ingestion.py -k build_review_candidate -q`
Expected: FAIL because `build_review_candidate` and `ReviewQueue` do not exist.

- [ ] **Step 3: Write minimal implementation**

```python
# app/models/ingestion.py
from typing import Optional

from sqlmodel import Field, SQLModel


class ReviewQueue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(..., nullable=False)
    entity_id: int = Field(..., nullable=False, index=True)
    diff_summary: list[str] = Field(default_factory=list, nullable=False)
    has_changes: bool = Field(..., nullable=False)
    status: str = Field(..., nullable=False)

# app/services/ingestion.py
from typing import Mapping

from sqlmodel import Session

from app.models.ingestion import ReviewQueue

TRACKED_FIELDS = ('summary', 'strengths', 'suitable_for', 'risks')


def build_review_candidate(
    session: Session,
    entity_type: str,
    entity_id: int,
    current_payload: Mapping[str, object],
    crawled_payload: Mapping[str, object],
) -> dict[str, object]:
    changed_fields = [
        field
        for field in TRACKED_FIELDS
        if current_payload.get(field) != crawled_payload.get(field)
    ]

    candidate = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "diff_summary": changed_fields,
        "has_changes": bool(changed_fields),
        "status": "pending_review" if changed_fields else "no_change",
    }

    review = ReviewQueue(
        entity_type=entity_type,
        entity_id=entity_id,
        diff_summary=changed_fields,
        has_changes=bool(changed_fields),
        status=candidate["status"],
    )
    session.add(review)
    session.flush()
    return candidate
```

- [ ] **Step 4: Run test again**

Run: `pytest tests/test_ingestion.py -k build_review_candidate -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```
git add app/models/ingestion.py app/services/ingestion.py tests/test_ingestion.py
git commit -m "feat: add ingestion diff and review queue"
```
