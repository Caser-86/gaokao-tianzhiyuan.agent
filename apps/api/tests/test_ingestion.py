from sqlmodel import Session, SQLModel, create_engine, select

from app.services.ingestion import build_review_candidate
from app.models.ingestion import ReviewQueue


def test_build_review_candidate_detects_tracked_field_changes():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    current_payload = {
        "summary": "old summary",
        "strengths": "old strengths",
        "suitable_for": "old audience",
        "risks": "old risks",
    }
    crawled_payload = current_payload.copy()
    crawled_payload["strengths"] = "new strengths"

    with Session(engine) as session:
        candidate = build_review_candidate(
            session=session,
            entity_type="school_content_version",
            entity_id=1,
            current_payload=current_payload,
            crawled_payload=crawled_payload,
        )

        assert candidate["entity_type"] == "school_content_version"
        assert candidate["entity_id"] == 1
        assert candidate["diff_summary"] == ["strengths"]
        assert candidate["has_changes"] is True
        assert candidate["status"] == "pending_review"

        review = session.exec(select(ReviewQueue)).one()
        assert review.diff_summary == ["strengths"]
        assert review.has_changes is True
        assert review.status == "pending_review"
