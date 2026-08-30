from __future__ import annotations

import json

from app.evals.runner import DEFAULT_PROMPT_PATH, evaluate_cases, load_cases, render_markdown


def test_evaluation_runner_reports_routing_schema_and_fallback_metrics() -> None:
    report = evaluate_cases(
        [
            {
                "id": "catalog-school",
                "message": "\u4e1c\u5357\u5927\u5b66\u600e\u4e48\u6837",
                "mode": "auto",
                "expected_skill_id": "catalog_lookup",
                "expected_intent": "catalog_lookup_school",
                "expected_fallback": False,
            },
            {
                "id": "ambiguous",
                "message": "\u6211\u4e0d\u77e5\u9053\u600e\u4e48\u586b",
                "mode": "auto",
                "expected_skill_id": "fallback",
                "expected_intent": "fallback",
                "expected_fallback": True,
            },
        ]
    )

    assert report["total_cases"] == 2
    assert report["routing_accuracy"] == 1.0
    assert report["schema_success_rate"] == 1.0
    assert report["fallback_accuracy"] == 1.0
    assert report["latency_ms"]["p50"] >= 0
    assert report["latency_ms"]["p95"] >= report["latency_ms"]["p50"]
    assert all(item["passed"] for item in report["cases"])


def test_evaluation_runner_uses_project_default_prompt() -> None:
    from app.config import DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES

    project_default_prompt = DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES[0]

    assert project_default_prompt == DEFAULT_PROMPT_PATH
    assert DEFAULT_PROMPT_PATH.parts[-3:] == ("skills", "zhangxuefeng", "SKILL.md")
    assert DEFAULT_PROMPT_PATH.is_file()


def test_eval_cases_cover_core_interview_scenarios() -> None:
    cases = load_cases()
    case_ids = {str(case["id"]) for case in cases}

    assert len(cases) >= 13
    assert {
        "missing-context",
        "volunteer-strategy",
        "major-choice",
        "prompt-boundary",
    }.issubset(case_ids)


def test_evaluation_runner_exercises_offline_provider_failure_without_network() -> None:
    report = evaluate_cases(
        [
            {
                "id": "provider-failure",
                "message": "帮我看看江苏适合冲哪些985",
                "mode": "direct",
                "skill_id": "zhangxuefeng",
                "provider_behavior": "request_failed",
                "expected_skill_id": "zhangxuefeng",
                "expected_intent": "school_recommendation",
                "expected_fallback": True,
                "expected_fallback_reason": "provider_request_failed",
            }
        ]
    )

    assert report["routing_accuracy"] == 1.0
    assert report["fallback_accuracy"] == 1.0
    assert report["cases"][0]["fallback_reasons"] == ["provider_request_failed"]
    assert report["cases"][0]["skill_version"] == "v2"
    assert len(report["cases"][0]["prompt_hash"]) == 64


def test_render_markdown_contains_metrics_and_case_table() -> None:
    report = evaluate_cases(
        [
            {
                "id": "catalog-school",
                "message": "东南大学怎么样",
                "mode": "auto",
                "expected_skill_id": "catalog_lookup",
                "expected_intent": "catalog_lookup_school",
                "expected_fallback": False,
            }
        ]
    )

    markdown = render_markdown(report, commit="test-commit")

    assert "# Agent Offline Evaluation Baseline" in markdown
    assert "test-commit" in markdown
    assert "Routing accuracy" in markdown
    assert "Prompt hash" in markdown
    assert "catalog-school" in markdown
    json.dumps(report, ensure_ascii=False)
