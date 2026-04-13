from typing import Mapping

from sqlmodel import Session

from app.models.ingestion import ReviewQueue

TRACKED_FIELDS = ("summary", "strengths", "suitable_for", "risks")


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

    status = "pending_review" if changed_fields else "no_change"
    candidate = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "diff_summary": changed_fields,
        "has_changes": bool(changed_fields),
        "status": status,
    }

    review = ReviewQueue(
        entity_type=entity_type,
        entity_id=entity_id,
        diff_summary=changed_fields,
        has_changes=candidate["has_changes"],
        status=status,
    )
    session.add(review)
    session.flush()

    return candidate
