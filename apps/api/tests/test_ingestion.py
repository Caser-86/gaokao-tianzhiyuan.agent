import pytest
from sqlmodel import SQLModel, Session, create_engine

from app.models.ingestion import ReviewQueue
from app.services.ingestion import build_review_candidate, build_review_queue_payload


def test_build_review_candidate_detects_summary_changes() -> None:
    current_payload = {"summary": "old summary", "strengths": "strong faculty"}
    crawled_payload = {"summary": "new summary", "strengths": "strong faculty"}

    candidate = build_review_candidate(
        entity_type="school",
        entity_id=1,
        current_payload=current_payload,
        crawled_payload=crawled_payload,
    )

    assert candidate["has_changes"] is True
    assert candidate["diff_summary"] == ["summary"]
    assert candidate["status"] == "pending_review"


def test_build_review_candidate_returns_no_change_without_diffs() -> None:
    current_payload = {"summary": "same summary", "strengths": "strong faculty"}
    crawled_payload = {"summary": "same summary", "strengths": "strong faculty"}

    candidate = build_review_candidate(
        entity_type="school",
        entity_id=2,
        current_payload=current_payload,
        crawled_payload=crawled_payload,
    )

    assert candidate["has_changes"] is False
    assert candidate["diff_summary"] == []
    assert candidate["status"] == "no_change"


@pytest.mark.parametrize(
    ("current_summary", "crawled_summary", "expected_status"),
    [
        ("old summary", "new summary", "pending_review"),
        ("same summary", "same summary", "no_change"),
    ],
)
def test_build_review_queue_payload_maps_status_to_review_status(
    current_summary: str, crawled_summary: str, expected_status: str
) -> None:
    candidate = build_review_candidate(
        entity_type="school",
        entity_id=3,
        current_payload={"summary": current_summary},
        crawled_payload={"summary": crawled_summary},
    )
    payload = build_review_queue_payload(candidate)

    assert "status" not in payload
    assert payload["review_status"] == expected_status

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        queue_row = ReviewQueue(**payload)
        session.add(queue_row)
        session.commit()
        session.refresh(queue_row)

        assert queue_row.review_status == expected_status
