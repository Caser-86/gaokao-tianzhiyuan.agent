from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections.abc import Callable, Iterable
from math import ceil
from pathlib import Path
from typing import Any

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from .. import models  # noqa: F401  # Registers every table before create_all.
from ..models.catalog import SchoolMajorRelation
from ..scripts.seed_catalog import (
    load_catalog as load_seed_catalog,
)
from ..scripts.seed_catalog import (
    sync_major_ranking_references,
    sync_school_major_relations,
    sync_school_ranking_references,
    upsert_major,
    upsert_school,
    upsert_search_entry,
)
from ..services.access_control import set_smart_analysis_mode, set_user_entitlement
from ..services.chat import ConversationService
from ..services.llm import ProviderRequestError
from ..services.skills import CatalogLookupSkill, SkillRegistry, ZhangXueFengSkill

REQUIRED_CONTENT_KEYS = {
    "intent",
    "summary",
    "entities",
    "analysis",
    "suggestions",
    "follow_up_questions",
    "actions",
    "risk_flags",
    "rendered_reply",
}
DEFAULT_CASES_PATH = Path(__file__).resolve().parents[2] / "evals" / "cases.json"
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[2] / "evals" / "offline-prompt.md"


class _OfflineProvider:
    def __init__(self, behavior: str) -> None:
        self.behavior = behavior

    def complete_text(self, *, messages: list[Any]) -> str:
        _ = messages
        if self.behavior == "request_failed":
            raise ProviderRequestError("offline provider failure")
        if self.behavior == "insufficient_balance":
            raise ProviderRequestError(
                "offline provider balance failure",
                reason="insufficient_balance",
            )
        if self.behavior == "invalid_json":
            return "not-json"
        return json.dumps(
            {
                "intent": "school_recommendation",
                "summary": "offline evaluation structured result",
                "entities": {"province": "Jiangsu"},
                "analysis": "This is a fixed Provider output with no network access.",
                "suggestions": [],
                "follow_up_questions": [],
                "actions": [],
                "risk_flags": [],
                "rendered_reply": "Offline evaluation passed the structured output check.",
            },
            ensure_ascii=False,
        )


def load_cases(path: str | Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ValueError("evaluation cases must be a JSON array of objects")
    return [dict(item) for item in raw]


def _build_registry(
    provider_behavior: str | None,
    *,
    session_factory: Callable[[], Session],
) -> SkillRegistry:
    provider = _OfflineProvider(provider_behavior) if provider_behavior else None
    return SkillRegistry(
        [
            ZhangXueFengSkill(
                provider=provider,
                skill_prompt_path=str(DEFAULT_PROMPT_PATH),
            ),
            CatalogLookupSkill(session_factory=session_factory),
        ]
    )


def _build_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    _seed_eval_catalog(engine)
    return engine


def _seed_eval_catalog(engine) -> None:
    catalog = load_seed_catalog()
    with Session(engine) as session:
        upsert_search_entry(session, catalog)
        school_map = {}
        for school_data in catalog.get("schools", []):
            school = upsert_school(session, school_data)
            school_map[school.slug] = school
            sync_school_ranking_references(
                session,
                school,
                school_data.get("ranking_references", []),
            )

        major_map = {}
        major_slug_to_id = {}
        for major_data in catalog.get("majors", []):
            major = upsert_major(session, major_data)
            major_map[major.slug] = major
            major_slug_to_id[major.slug] = major.id
            sync_major_ranking_references(
                session,
                major,
                major_data.get("ranking_references", []),
            )

        for school_data in catalog.get("schools", []):
            school = school_map.get(school_data["slug"])
            if school is not None:
                sync_school_major_relations(
                    session,
                    school,
                    school_data.get("related_majors", []),
                    major_slug_to_id,
                )

        seen_relations = {
            (relation.school_id, relation.major_id)
            for relation in session.exec(select(SchoolMajorRelation)).all()
        }
        school_slug_to_id = {school.slug: school.id for school in school_map.values()}
        for major_data in catalog.get("majors", []):
            major = major_map.get(major_data["slug"])
            if major is None:
                continue
            for school_slug in major_data.get("related_schools", []):
                school_id = school_slug_to_id.get(school_slug)
                if school_id is None or (school_id, major.id) in seen_relations:
                    continue
                seen_relations.add((school_id, major.id))
                session.add(SchoolMajorRelation(school_id=school_id, major_id=major.id))
        session.commit()


def _seed_eval_access_policy(engine, *, user_id: str, case: dict[str, Any]) -> None:
    mode = str(case.get("server_smart_analysis_mode", "on")).strip().lower()
    entitlements = case.get("server_entitlements", [])
    if not isinstance(entitlements, list):
        entitlements = []

    with Session(engine) as session:
        set_smart_analysis_mode(session, mode)
        for entitlement in entitlements:
            normalized_entitlement = str(entitlement).strip()
            if normalized_entitlement:
                set_user_entitlement(
                    session,
                    user_id=user_id,
                    entitlement=normalized_entitlement,
                    is_enabled=True,
                )


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, ceil(len(ordered) * fraction) - 1))
    return round(ordered[index], 2)


def _evaluate_case(case: dict[str, Any], engine) -> dict[str, Any]:
    case_id = str(case.get("id", "")).strip()
    user_id = f"eval-{case_id or 'case'}"
    session_id = f"eval-session-{case_id or 'case'}"
    traces: list[dict[str, Any]] = []

    _seed_eval_access_policy(engine, user_id=user_id, case=case)

    def session_factory() -> Session:
        return Session(engine)

    service = ConversationService(
        registry=_build_registry(
            case.get("provider_behavior"),
            session_factory=session_factory,
        ),
        session_factory=session_factory,
        trace_sink=traces.append,
    )
    started_at = time.perf_counter()
    response = service.handle_message(
        channel="web",
        user_id=user_id,
        message=str(case.get("message", "")),
        session_id=session_id,
        skill_id=("zhangxuefeng" if case.get("mode") == "direct" else None),
        metadata={"smart_analysis_mode": "on"},
    )
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

    content = response["output"]["content"]
    trace = traces[0] if traces else {}
    selected_skill = trace.get("selected_skill") or {}
    matched_skill_id = response["matched_skill"]["skill_id"]
    fallback_reasons = list(trace.get("fallback_reasons", []))
    schema_ok = (
        response["output"]["type"] == "structured_json"
        and isinstance(content, dict)
        and REQUIRED_CONTENT_KEYS.issubset(content)
    )
    route_ok = matched_skill_id == case.get("expected_skill_id")
    intent_ok = content.get("intent") == case.get("expected_intent")
    fallback_ok = response["debug"]["used_fallback"] == case.get("expected_fallback")
    expected_reason = case.get("expected_fallback_reason")
    reason_ok = expected_reason is None or expected_reason in fallback_reasons

    return {
        "id": case_id,
        "passed": all((schema_ok, route_ok, intent_ok, fallback_ok, reason_ok)),
        "latency_ms": latency_ms,
        "matched_skill_id": matched_skill_id,
        "skill_version": selected_skill.get("version"),
        "prompt_hash": selected_skill.get("prompt_hash"),
        "intent": content.get("intent"),
        "used_fallback": response["debug"]["used_fallback"],
        "fallback_reasons": fallback_reasons,
        "checks": {
            "schema": schema_ok,
            "routing": route_ok,
            "intent": intent_ok,
            "fallback": fallback_ok,
            "fallback_reason": reason_ok,
        },
    }


def evaluate_cases(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    case_list = [dict(case) for case in cases]
    engine = _build_engine()
    try:
        results = [_evaluate_case(case, engine) for case in case_list]
    finally:
        engine.dispose()

    total = len(results)
    latencies = [float(item["latency_ms"]) for item in results]
    denominator = total or 1
    return {
        "total_cases": total,
        "passed_cases": sum(1 for item in results if item["passed"]),
        "routing_accuracy": round(
            sum(1 for item in results if item["checks"]["routing"]) / denominator,
            4,
        ),
        "schema_success_rate": round(
            sum(1 for item in results if item["checks"]["schema"]) / denominator,
            4,
        ),
        "fallback_accuracy": round(
            sum(1 for item in results if item["checks"]["fallback"]) / denominator,
            4,
        ),
        "latency_ms": {
            "p50": _percentile(latencies, 0.5),
            "p95": _percentile(latencies, 0.95),
        },
        "cases": results,
    }


def render_markdown(report: dict[str, Any], *, commit: str = "working-tree") -> str:
    lines = [
        "# Agent Offline Evaluation Baseline",
        "",
        f"> Commit: `{commit}`  ",
        "> Run mode: fixed JSON cases + local Skills + an offline Provider stub; no real model access.",
        "",
        "## Metrics",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Cases | {report['total_cases']} |",
        f"| Passed | {report['passed_cases']} |",
        f"| Routing accuracy | {report['routing_accuracy']:.2%} |",
        f"| Schema success rate | {report['schema_success_rate']:.2%} |",
        f"| Fallback accuracy | {report['fallback_accuracy']:.2%} |",
        f"| P50 latency (local) | {report['latency_ms']['p50']:.2f} ms |",
        f"| P95 latency (local) | {report['latency_ms']['p95']:.2f} ms |",
        "",
        "## Case Results",
        "",
        "| Case | Passed | Skill | Version | Prompt hash | Intent | Fallback | Latency |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for case in report["cases"]:
        lines.append(
            f"| `{case['id']}` | {'yes' if case['passed'] else 'no'} | "
            f"`{case['matched_skill_id']}` | `{case['skill_version'] or '-'}` | "
            f"`{case['prompt_hash'] or '-'}` | `{case['intent']}` | "
            f"`{case['used_fallback']}` | {case['latency_ms']:.2f} ms |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "These metrics describe this commit under fixed cases and offline configuration; they do not represent online model quality, admission advice accuracy, or production latency.",
            "",
        ]
    )
    return "\n".join(lines)


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "working-tree"
    return result.stdout.strip() or "working-tree"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline Agent evaluation set")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()

    report = evaluate_cases(load_cases(args.cases))
    output = (
        json.dumps(report, ensure_ascii=False, indent=2)
        if args.format == "json"
        else render_markdown(report, commit=args.commit or _git_commit())
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    raise SystemExit(0 if report["passed_cases"] == report["total_cases"] else 1)


if __name__ == "__main__":
    main()
