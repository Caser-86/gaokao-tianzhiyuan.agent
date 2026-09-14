from __future__ import annotations

import json
from pathlib import Path

import pytest

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
    from app.config import (
        DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES,
        resolve_zhangxuefeng_skill_path,
    )

    project_default_prompt = DEFAULT_ZHANGXUEFENG_SKILL_CANDIDATES[0]

    assert Path(resolve_zhangxuefeng_skill_path("")) == DEFAULT_PROMPT_PATH
    assert project_default_prompt == DEFAULT_PROMPT_PATH
    assert DEFAULT_PROMPT_PATH.parts[-3:] == ("skills", "zhangxuefeng", "SKILL.md")
    assert DEFAULT_PROMPT_PATH.is_file()


def test_evaluation_runner_checks_expected_risk_flags() -> None:
    report = evaluate_cases(
        [
            {
                "id": "missing-candidate-context",
                "message": "江苏985",
                "mode": "direct",
                "skill_id": "zhangxuefeng",
                "expected_skill_id": "zhangxuefeng",
                "expected_intent": "school_recommendation",
                "expected_fallback": True,
                "expected_risk_flags": ["insufficient_candidate_context"],
            }
        ]
    )

    assert report["cases"][0]["passed"] is True
    assert report["cases"][0]["checks"]["risk_flags"] is True


def test_evaluation_report_declares_shared_prompt_identity() -> None:
    report = evaluate_cases(
        [
            {
                "id": "prompt-identity",
                "message": "江苏考生620分怎么选学校",
                "mode": "direct",
                "skill_id": "zhangxuefeng",
                "provider_behavior": "success",
                "expected_skill_id": "zhangxuefeng",
                "expected_intent": "school_recommendation",
                "expected_fallback": False,
            }
        ]
    )

    prompt = report["prompt"]

    assert prompt["path"] == "skills/zhangxuefeng/SKILL.md"
    assert len(prompt["sha256"]) == 64
    assert prompt["sha256"] == report["cases"][0]["prompt_hash"]
    assert len(prompt["asset_sha256"]) == 64
    assert len(prompt["effective_sha256"]) == 64
    assert prompt["asset_sha256"] == prompt["sha256"]
    assert prompt["effective_sha256"] == report["cases"][0]["effective_prompt_hash"]


def test_evaluation_runner_accepts_custom_prompt_and_records_effective_identity(tmp_path) -> None:
    custom_prompt = tmp_path / "custom-SKILL.md"
    custom_prompt.write_text("CUSTOM PROMPT", encoding="utf-8")

    report = evaluate_cases(
        [
            {
                "id": "custom-prompt",
                "message": "江苏考生620分怎么选学校",
                "mode": "direct",
                "skill_id": "zhangxuefeng",
                "provider_behavior": "success",
                "expected_skill_id": "zhangxuefeng",
                "expected_intent": "school_recommendation",
                "expected_fallback": False,
            }
        ],
        prompt_path=custom_prompt,
    )

    assert report["prompt"]["path"] == str(custom_prompt)
    assert report["prompt"]["asset_sha256"] != report["prompt"]["effective_sha256"]
    assert report["cases"][0]["prompt_hash"] == report["prompt"]["asset_sha256"]
    assert report["cases"][0]["effective_prompt_hash"] == report["prompt"]["effective_sha256"]


def test_evaluation_runner_fails_fast_when_prompt_is_missing(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        evaluate_cases(
            [
                {
                    "id": "missing-prompt",
                    "message": "江苏考生620分怎么选学校",
                    "mode": "direct",
                    "skill_id": "zhangxuefeng",
                    "provider_behavior": "success",
                    "expected_skill_id": "zhangxuefeng",
                    "expected_intent": "school_recommendation",
                    "expected_fallback": False,
                }
            ],
            prompt_path=tmp_path / "does-not-exist.md",
        )


def test_eval_cases_cover_core_interview_scenarios() -> None:
    cases = load_cases()
    case_ids = {str(case["id"]) for case in cases}

    assert len(cases) >= 30
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
    assert "Prompt source" in markdown
    assert "Prompt hash" in markdown
    assert "Effective prompt SHA-256" in markdown
    assert "Evaluation mode" in markdown
    assert "catalog-school" in markdown
    json.dumps(report, ensure_ascii=False)
