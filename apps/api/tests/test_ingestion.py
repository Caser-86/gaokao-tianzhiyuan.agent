from app.services.ingestion import build_review_candidate


def test_build_review_candidate_detects_summary_changes() -> None:
    current_payload = {"summary": "老版本摘要", "strengths": "计算机、电子信息"}
    crawled_payload = {"summary": "新版本摘要", "strengths": "计算机、电子信息"}

    candidate = build_review_candidate(
        entity_type="school",
        entity_id=1,
        current_payload=current_payload,
        crawled_payload=crawled_payload,
    )

    assert candidate["has_changes"] is True
    assert candidate["diff_summary"] == ["summary"]
    assert candidate["status"] == "pending_review"
