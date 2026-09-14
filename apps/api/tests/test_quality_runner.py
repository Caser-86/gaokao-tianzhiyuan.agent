from __future__ import annotations

import pytest

from app.evals.quality_runner import (
    DEFAULT_DOMAIN_CASES_PATH,
    evaluate_quality_cases,
    load_quality_cases,
    render_quality_markdown,
)


def test_domain_quality_dataset_has_expected_balanced_categories() -> None:
    cases = load_quality_cases()
    categories = {str(case["category"]) for case in cases}

    assert DEFAULT_DOMAIN_CASES_PATH.is_file()
    assert len(cases) == 40
    assert categories == {
        "missing-information",
        "citation-qa",
        "comparison",
        "multi-turn",
        "adversarial",
        "out-of-domain",
    }
    assert {
        category: sum(case["category"] == category for case in cases) for category in categories
    } == {
        "missing-information": 8,
        "citation-qa": 8,
        "comparison": 6,
        "multi-turn": 6,
        "adversarial": 6,
        "out-of-domain": 6,
    }
    assert {str(case["split"]) for case in cases} == {"dev", "holdout"}


def test_quality_runner_replay_reports_quality_metrics_and_failure_samples() -> None:
    report = evaluate_quality_cases()

    assert report["mode"] == "replay"
    assert report["total_cases"] == 40
    assert report["sample_denominators"] == {
        "citation_correctness": 40,
        "no_unsupported_numbers": 40,
        "follow_up_coverage": 40,
        "type_contract": 40,
    }
    assert report["metrics"]["citation_correctness"] == 1.0
    assert report["metrics"]["no_unsupported_numbers"] == 1.0
    assert report["metrics"]["follow_up_coverage"] == 1.0
    assert report["metrics"]["type_contract"] == 1.0
    assert report["model"] is None
    assert report["cost_yuan"] == 0.0
    assert report["failure_samples"] == []
    assert report["category_counts"]["missing-information"] == 8
    assert report["category_counts"]["citation-qa"] == 8
    assert report["split_counts"] == {"dev": 26, "holdout": 14}

    markdown = render_quality_markdown(report)
    assert "# Domain Quality Evaluation" in markdown
    assert "Replay only" in markdown
    assert "Sample denominators" in markdown


def test_quality_runner_exposes_failures_without_hiding_the_denominator() -> None:
    cases = [
        {
            "id": "bad-replay",
            "category": "citation-qa",
            "split": "holdout",
            "message": "东南大学的证据是什么？",
            "evidence_ids": ["school-1"],
            "required_evidence_ids": ["school-1"],
            "required_follow_up_terms": [],
            "forbidden_patterns": [],
            "replay_output": {
                "intent": "school_recommendation",
                "rendered_reply": "录取概率 99%",
                "follow_up_questions": [],
                "evidence_refs": ["unknown-evidence"],
            },
        }
    ]

    report = evaluate_quality_cases(cases)

    assert report["total_cases"] == 1
    assert report["passed_cases"] == 0
    assert report["metrics"]["citation_correctness"] == 0.0
    assert report["metrics"]["no_unsupported_numbers"] == 0.0
    assert report["sample_denominators"]["citation_correctness"] == 1
    assert report["failure_samples"][0]["id"] == "bad-replay"
    assert "citation_correctness" in report["failure_samples"][0]["failed_checks"]


def test_quality_runner_real_mode_requires_explicit_budgets() -> None:
    with pytest.raises(ValueError, match="budget"):
        evaluate_quality_cases(mode="real")
