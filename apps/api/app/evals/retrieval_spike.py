from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from sqlmodel import Session

from ..services.skills import CatalogLookupSkill, ChatRequestContext
from .runner import _build_engine

DEFAULT_CASES_PATH = Path(__file__).resolve().parents[2] / "evals" / "retrieval-cases.json"


def load_retrieval_cases(path: str | Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ValueError("retrieval cases must be a JSON array of objects")
    return [dict(item) for item in raw]


def evaluate_retrieval_cases(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    case_list = [dict(case) for case in cases]
    engine = _build_engine()

    def session_factory() -> Session:
        return Session(engine)

    skill = CatalogLookupSkill(session_factory=session_factory)
    results: list[dict[str, Any]] = []
    try:
        for case in case_list:
            match = skill.match(
                ChatRequestContext(
                    channel="web",
                    user_id="eval-retrieval",
                    message=str(case.get("message", "")),
                )
            )
            actual_covered = bool(match.matched)
            expected_covered = bool(case.get("expected_sql_covered"))
            results.append(
                {
                    "id": str(case.get("id", "")).strip(),
                    "sql_covered": actual_covered,
                    "expected_sql_covered": expected_covered,
                    "confidence": round(float(match.confidence), 4),
                    "reason": match.reason,
                    "label_correct": actual_covered == expected_covered,
                }
            )
    finally:
        engine.dispose()

    total = len(results)
    denominator = total or 1
    false_negatives = [
        item["id"] for item in results if item["expected_sql_covered"] and not item["sql_covered"]
    ]
    false_positives = [
        item["id"] for item in results if item["sql_covered"] and not item["expected_sql_covered"]
    ]
    label_accuracy = sum(item["label_correct"] for item in results) / denominator
    recommendation = (
        "keep_sql_first"
        if not false_negatives and not false_positives and total <= 50
        else "collect_more_evidence"
    )
    return {
        "total_cases": total,
        "sql_coverage": round(sum(item["sql_covered"] for item in results) / denominator, 4),
        "expected_sql_coverage": round(
            sum(item["expected_sql_covered"] for item in results) / denominator,
            4,
        ),
        "label_accuracy": round(label_accuracy, 4),
        "false_negative_ids": false_negatives,
        "false_positive_ids": false_positives,
        "uncovered_case_ids": [item["id"] for item in results if not item["sql_covered"]],
        "recommendation": recommendation,
        "cases": results,
    }


def render_markdown(report: dict[str, Any], *, commit: str = "working-tree") -> str:
    lines = [
        "# SQL Coverage Spike",
        "",
        f"> Commit: `{commit}`  ",
        "> Scope: quantify the boundary of the existing structured SQL catalog before considering vector retrieval.",
        "",
        "## Metrics",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Cases | {report['total_cases']} |",
        f"| Observed SQL coverage | {report['sql_coverage']:.2%} |",
        f"| Expected SQL coverage | {report['expected_sql_coverage']:.2%} |",
        f"| Label agreement | {report['label_accuracy']:.2%} |",
        f"| Recommendation | `{report['recommendation']}` |",
        "",
        "## Cases",
        "",
        "| Case | SQL covered | Expected | Confidence | Reason |",
        "|---|---|---|---:|---|",
    ]
    for case in report["cases"]:
        lines.append(
            f"| `{case['id']}` | `{case['sql_covered']}` | "
            f"`{case['expected_sql_covered']}` | {case['confidence']:.2f} | "
            f"{case['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "No vector dependency is added. Known school/major lookup is covered by the structured catalog; uncovered cases are open-ended strategy, out-of-catalog, or non-entity questions and should first go through the existing Skill/fallback path. Expand the fixed set before revisiting retrieval architecture.",
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
    parser = argparse.ArgumentParser(description="Measure structured SQL catalog coverage")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()

    report = evaluate_retrieval_cases(load_retrieval_cases(args.cases))
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report, commit=args.commit or _git_commit()))
    raise SystemExit(0 if report["recommendation"] == "keep_sql_first" else 1)


if __name__ == "__main__":
    main()
