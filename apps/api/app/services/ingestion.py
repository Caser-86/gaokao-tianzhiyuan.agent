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


def build_review_queue_payload(candidate: Mapping[str, object]) -> dict[str, object]:
    """Map service candidate output into the ReviewQueue schema."""
    status = candidate.get("status")
    if not isinstance(status, str):
        raise ValueError("Review candidate must include string field 'status'.")

    entity_type = candidate.get("entity_type")
    if not isinstance(entity_type, str):
        raise ValueError("Review candidate must include string field 'entity_type'.")

    entity_id = candidate.get("entity_id")
    if not isinstance(entity_id, int):
        raise ValueError("Review candidate must include integer field 'entity_id'.")

    diff_summary = candidate.get("diff_summary")
    if not isinstance(diff_summary, list):
        raise ValueError("Review candidate must include list field 'diff_summary'.")

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "diff_summary": diff_summary.copy(),
        "review_status": status,
    }
