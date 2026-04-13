from typing import Mapping

TRACKED_FIELDS = ("summary", "strengths", "suitable_for", "risks")


def build_review_candidate(
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

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "diff_summary": changed_fields,
        "has_changes": bool(changed_fields),
        "status": status,
    }
