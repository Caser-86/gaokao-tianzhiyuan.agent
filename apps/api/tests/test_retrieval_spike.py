from __future__ import annotations

from app.evals.retrieval_spike import evaluate_retrieval_cases, render_markdown


def test_retrieval_spike_reports_sql_coverage_and_uncovered_cases() -> None:
    report = evaluate_retrieval_cases(
        [
            {
                "id": "known-school",
                "message": "东南大学怎么样",
                "expected_sql_covered": True,
            },
            {
                "id": "open-ended-fit",
                "message": "我适合什么专业",
                "expected_sql_covered": False,
            },
        ]
    )

    assert report["total_cases"] == 2
    assert report["sql_coverage"] == 0.5
    assert report["label_accuracy"] == 1.0
    assert report["uncovered_case_ids"] == ["open-ended-fit"]
    assert report["recommendation"] == "keep_sql_first"


def test_retrieval_spike_markdown_explains_why_no_vector_dependency_is_added() -> None:
    report = evaluate_retrieval_cases(
        [
            {
                "id": "known-major",
                "message": "临床医学专业介绍",
                "expected_sql_covered": True,
            }
        ]
    )

    markdown = render_markdown(report, commit="test-commit")

    assert "SQL Coverage Spike" in markdown
    assert "test-commit" in markdown
    assert "keep_sql_first" in markdown
    assert "No vector dependency" in markdown
