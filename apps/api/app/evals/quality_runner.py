from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path
from typing import Any

DEFAULT_DOMAIN_CASES_PATH = Path(__file__).resolve().parents[2] / "evals" / "domain-cases.json"
DEFAULT_COMPARISON_CASES_PATH = (
    Path(__file__).resolve().parents[2] / "evals" / "comparison-cases.json"
)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
ALLOWED_INTENTS = {
    "school_recommendation",
    "major_recommendation",
    "volunteer_strategy",
    "comparison",
    "fallback",
}
QUALITY_CHECKS = (
    "citation_correctness",
    "no_unsupported_numbers",
    "follow_up_coverage",
    "type_contract",
)
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?%?")


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _hash_cases(cases: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        cases,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "working-tree"
    return result.stdout.strip() or "working-tree"


def _git_dirty() -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def load_quality_cases(path: str | Path = DEFAULT_DOMAIN_CASES_PATH) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ValueError("domain quality cases must be a JSON array of objects")
    return [dict(item) for item in raw]


def _evidence_refs(output: Any) -> Any:
    """Read the runtime nested citation field and legacy fixture field."""

    if not isinstance(output, dict):
        return None
    if "evidence_refs" in output:
        return output.get("evidence_refs")
    entities = output.get("entities")
    if isinstance(entities, dict):
        return entities.get("evidence_refs")
    return None


def _type_contract_ok(output: Any) -> bool:
    refs = _evidence_refs(output)
    return (
        isinstance(output, dict)
        and isinstance(output.get("intent"), str)
        and output["intent"] in ALLOWED_INTENTS
        and isinstance(output.get("rendered_reply"), str)
        and isinstance(output.get("follow_up_questions"), list)
        and all(isinstance(item, str) for item in output["follow_up_questions"])
        and isinstance(refs, list)
        and all(isinstance(item, str) for item in refs)
    )


def _citation_correct(output: dict[str, Any], case: dict[str, Any]) -> bool:
    refs = _evidence_refs(output)
    evidence_ids = case.get("evidence_ids", [])
    required_ids = case.get("required_evidence_ids", [])
    if not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        return False
    if not isinstance(evidence_ids, list) or not isinstance(required_ids, list):
        return False
    return all(ref in evidence_ids for ref in refs) and all(
        evidence_id in refs for evidence_id in required_ids
    )


def _no_unsupported_numbers(output: dict[str, Any], case: dict[str, Any]) -> bool:
    text = "\n".join(
        [
            str(output.get("rendered_reply", "")),
            *[str(item) for item in output.get("follow_up_questions", [])],
        ]
    )
    if not NUMBER_PATTERN.search(text):
        return True
    # A numeric claim is only considered supported when this answer cites at
    # least one evidence item that belongs to the fixed input package.
    refs = _evidence_refs(output) or []
    evidence_ids = case.get("evidence_ids", [])
    return isinstance(refs, list) and any(ref in evidence_ids for ref in refs)


def _follow_up_coverage(output: dict[str, Any], case: dict[str, Any]) -> bool:
    required_terms = case.get("required_follow_up_terms", [])
    if not isinstance(required_terms, list) or not all(
        isinstance(item, str) for item in required_terms
    ):
        return False
    follow_up_text = "\n".join(
        [
            str(output.get("rendered_reply", "")),
            *[str(item) for item in output.get("follow_up_questions", [])],
        ]
    )
    return all(term in follow_up_text for term in required_terms)


def _forbidden_assertions_ok(output: dict[str, Any], case: dict[str, Any]) -> bool:
    text = json.dumps(output, ensure_ascii=False)
    patterns = case.get("forbidden_patterns", [])
    if not isinstance(patterns, list):
        return False
    return not any(re.search(str(pattern), text) for pattern in patterns)


def _score_quality_output(output: Any, case: dict[str, Any]) -> dict[str, bool]:
    output_dict = output if isinstance(output, dict) else {}
    checks = {
        "citation_correctness": _citation_correct(output_dict, case),
        "no_unsupported_numbers": _no_unsupported_numbers(output_dict, case),
        "follow_up_coverage": _follow_up_coverage(output_dict, case),
        "type_contract": _type_contract_ok(output),
    }
    checks["forbidden_assertions"] = _forbidden_assertions_ok(output_dict, case)
    return checks


def _failure_sample(
    case: dict[str, Any],
    output: Any,
    checks: dict[str, bool],
) -> dict[str, Any]:
    rendered_reply = output.get("rendered_reply", "") if isinstance(output, dict) else ""
    return {
        "id": str(case.get("id", "")),
        "category": str(case.get("category", "")),
        "split": str(case.get("split", "")),
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "reply_excerpt": str(rendered_reply)[:240],
    }


def evaluate_quality_cases(
    cases: Iterable[dict[str, Any]] | None = None,
    *,
    cases_path: str | Path = DEFAULT_DOMAIN_CASES_PATH,
    mode: str = "replay",
    max_cases: int | None = None,
    max_output_tokens: int = 0,
    max_cost_yuan: float = 0.0,
    model: str | None = None,
) -> dict[str, Any]:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"replay", "real"}:
        raise ValueError("quality evaluation mode must be replay or real")
    if normalized_mode == "real":
        if (max_cases or 0) <= 0 or max_output_tokens <= 0 or max_cost_yuan <= 0:
            raise ValueError(
                "real quality evaluation requires positive max_cases, "
                "max_output_tokens, and max_cost_yuan budget"
            )
        raise NotImplementedError(
            "real quality evaluation is intentionally not wired to a Provider yet; "
            "run replay or add an explicit Provider adapter"
        )

    case_list = [
        dict(case) for case in (cases if cases is not None else load_quality_cases(cases_path))
    ]
    if max_cases is not None:
        if max_cases <= 0:
            raise ValueError("max_cases must be positive")
        case_list = case_list[:max_cases]

    check_totals = Counter()
    category_totals = Counter(str(case.get("category", "")) for case in case_list)
    split_totals = Counter(str(case.get("split", "")) for case in case_list)
    failures: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    forbidden_violations = 0
    for case in case_list:
        output = case.get("replay_output")
        checks = _score_quality_output(output, case)
        if not checks["forbidden_assertions"]:
            forbidden_violations += 1
        for name in QUALITY_CHECKS:
            check_totals[name] += int(checks[name])
        passed = all(checks.values())
        result = {
            "id": str(case.get("id", "")),
            "category": str(case.get("category", "")),
            "split": str(case.get("split", "")),
            "passed": passed,
            "checks": checks,
        }
        results.append(result)
        if not passed and len(failures) < 10:
            failures.append(_failure_sample(case, output, checks))

    total = len(case_list)
    denominator = total or 1
    return {
        "mode": "replay",
        "model": None,
        "cost_yuan": 0.0,
        "dataset": {
            "path": _display_path(Path(cases_path)) if cases is None else "inline-cases",
            "sha256": _hash_cases(case_list),
        },
        "commit": _git_commit(),
        "working_tree_dirty": _git_dirty(),
        "category_counts": dict(sorted(category_totals.items())),
        "split_counts": dict(sorted(split_totals.items())),
        "total_cases": total,
        "passed_cases": sum(1 for item in results if item["passed"]),
        "metrics": {name: round(check_totals[name] / denominator, 4) for name in QUALITY_CHECKS},
        "sample_denominators": {name: total for name in QUALITY_CHECKS},
        "forbidden_violations": forbidden_violations,
        "failure_samples": failures,
        "cases": results,
    }


def evaluate_quality_comparison(
    cases: Iterable[dict[str, Any]] | None = None,
    *,
    cases_path: str | Path = DEFAULT_COMPARISON_CASES_PATH,
    max_cases: int | None = None,
) -> dict[str, Any]:
    """Score paired direct-vs-grounded outputs with one shared protocol.

    This is a replay evaluator. Each case must provide one question, a shared
    budget object, the requested model alias, and the model returned by each
    Provider call. A pair is comparable only when both returned model names
    are present and equal; the requested alias is recorded but never treated
    as the returned model version.
    """

    case_list = [
        dict(case) for case in (cases if cases is not None else load_quality_cases(cases_path))
    ]
    if max_cases is not None:
        if max_cases <= 0:
            raise ValueError("max_cases must be positive")
        case_list = case_list[:max_cases]

    direct_passed = 0
    grounded_passed = 0
    comparable_cases = 0
    winner_counts = Counter()
    request_models: set[str] = set()
    returned_models: set[str] = set()
    per_case: list[dict[str, Any]] = []
    for case in case_list:
        direct_output = case.get("direct_output")
        grounded_output = case.get("grounded_output")
        direct_checks = _score_quality_output(direct_output, case)
        grounded_checks = _score_quality_output(grounded_output, case)
        direct_ok = all(direct_checks.values())
        grounded_ok = all(grounded_checks.values())
        direct_passed += int(direct_ok)
        grounded_passed += int(grounded_ok)

        request_model = str(case.get("request_model", "")).strip()
        direct_returned_model = str(case.get("direct_returned_model", "")).strip()
        grounded_returned_model = str(case.get("grounded_returned_model", "")).strip()
        if request_model:
            request_models.add(request_model)
        for model_name in (direct_returned_model, grounded_returned_model):
            if model_name:
                returned_models.add(model_name)

        shared_budget = case.get("budget")
        if not isinstance(shared_budget, dict):
            comparable = False
            comparison_reason = "missing_shared_budget"
        elif not direct_returned_model or not grounded_returned_model:
            comparable = False
            comparison_reason = "missing_returned_model"
        elif direct_returned_model != grounded_returned_model:
            comparable = False
            comparison_reason = "returned_model_mismatch"
        else:
            comparable = True
            comparison_reason = "same_returned_model_and_shared_budget"

        if comparable:
            comparable_cases += 1
            if grounded_ok and not direct_ok:
                winner = "grounded"
            elif direct_ok and not grounded_ok:
                winner = "direct"
            elif direct_ok and grounded_ok:
                winner = "tie"
            else:
                direct_score = sum(direct_checks.values())
                grounded_score = sum(grounded_checks.values())
                winner = (
                    "grounded"
                    if grounded_score > direct_score
                    else "direct"
                    if direct_score > grounded_score
                    else "tie"
                )
        else:
            winner = "not_comparable"
        winner_counts[winner] += 1
        per_case.append(
            {
                "id": str(case.get("id", "")),
                "category": str(case.get("category", "")),
                "split": str(case.get("split", "")),
                "message": str(case.get("message", "")),
                "request_model": request_model or None,
                "returned_models": {
                    "direct": direct_returned_model or None,
                    "grounded": grounded_returned_model or None,
                },
                "budget": shared_budget,
                "comparable": comparable,
                "comparison_reason": comparison_reason,
                "direct": {
                    "passed": direct_ok,
                    "failed_checks": [name for name, passed in direct_checks.items() if not passed],
                },
                "grounded": {
                    "passed": grounded_ok,
                    "failed_checks": [
                        name for name, passed in grounded_checks.items() if not passed
                    ],
                },
                "winner": winner,
            }
        )

    total = len(case_list)
    denominator = total or 1
    return {
        "mode": "replay_pairwise",
        "dataset": {
            "path": _display_path(Path(cases_path)) if cases is None else "inline-cases",
            "sha256": _hash_cases(case_list),
        },
        "commit": _git_commit(),
        "working_tree_dirty": _git_dirty(),
        "total_cases": total,
        "comparable_cases": comparable_cases,
        "metrics": {
            "direct_pass_rate": round(direct_passed / denominator, 4),
            "grounded_pass_rate": round(grounded_passed / denominator, 4),
        },
        "sample_denominators": {
            "direct_pass_rate": total,
            "grounded_pass_rate": total,
            "comparable_cases": total,
        },
        "request_models": sorted(request_models),
        "returned_models": sorted(returned_models),
        "winner_counts": dict(sorted(winner_counts.items())),
        "per_case": per_case,
    }


def render_quality_comparison_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Direct vs Grounded Quality Comparison",
        "",
        "> Replay only: paired recorded outputs; no real model access.",
        f"> Dataset: `{report['dataset']['path']}`  ",
        f"> Dataset SHA-256: `{report['dataset']['sha256']}`  ",
        f"> Commit: `{report['commit']}`; working tree dirty: `{report['working_tree_dirty']}`",
        "",
        "## Metrics",
        "",
        "| Variant | Pass rate | Sample denominator |",
        "|---|---:|---:|",
        f"| Direct user question | {report['metrics']['direct_pass_rate']:.2%} | {report['sample_denominators']['direct_pass_rate']} |",
        f"| Context + evidence + validation | {report['metrics']['grounded_pass_rate']:.2%} | {report['sample_denominators']['grounded_pass_rate']} |",
        "",
        f"Comparable pairs: `{report['comparable_cases']}/{report['total_cases']}`  ",
        f"Requested model aliases: `{report['request_models']}`  ",
        f"Provider returned models: `{report['returned_models']}`",
        "",
        "## Per-case comparison",
        "",
        "| Case | Comparable | Direct failures | Grounded failures | Winner | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for item in report["per_case"]:
        lines.append(
            f"| `{item['id']}` | `{item['comparable']}` | "
            f"`{', '.join(item['direct']['failed_checks']) or 'none'}` | "
            f"`{', '.join(item['grounded']['failed_checks']) or 'none'}` | "
            f"`{item['winner']}` | `{item['comparison_reason']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "A replay pair demonstrates the scoring protocol and recorded failure reasons. It does not prove that evidence grounding always improves online quality or admission accuracy.",
            "",
        ]
    )
    return "\n".join(lines)


def render_quality_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Domain Quality Evaluation",
        "",
        "> Replay only: fixed synthetic cases and recorded outputs; no real model access.",
        f"> Dataset: `{report['dataset']['path']}`  ",
        f"> Dataset SHA-256: `{report['dataset']['sha256']}`  ",
        f"> Commit: `{report['commit']}`; working tree dirty: `{report['working_tree_dirty']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Result | Sample denominator |",
        "|---|---:|---:|",
    ]
    for name, value in report["metrics"].items():
        lines.append(f"| {name} | {value:.2%} | {report['sample_denominators'][name]} |")
    lines.extend(
        [
            f"| Forbidden assertion violations | {report['forbidden_violations']} | {report['total_cases']} |",
            "",
            "## Sample denominators",
            "",
            "The denominator is the number of cases included in this run; empty datasets are reported as zero cases with a denominator guard of one for arithmetic only.",
            "",
            "## Dataset distribution",
            "",
            "| Group | Counts |",
            "|---|---|",
            f"| Category | `{report['category_counts']}` |",
            f"| Split | `{report['split_counts']}` |",
            "",
            "## Failure samples",
            "",
        ]
    )
    if report["failure_samples"]:
        lines.extend(
            [
                "| Case | Split | Failed checks | Reply excerpt |",
                "|---|---|---|---|",
            ]
        )
        for sample in report["failure_samples"]:
            excerpt = sample["reply_excerpt"].replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| `{sample['id']}` | `{sample['split']}` | "
                f"`{', '.join(sample['failed_checks'])}` | {excerpt} |"
            )
    else:
        lines.append("No failed cases in this run.")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Replay metrics validate the evaluator and fixed response fixtures. They are not evidence of online model quality, admission accuracy, or production behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the domain quality evaluation set")
    parser.add_argument("--cases", default=str(DEFAULT_DOMAIN_CASES_PATH))
    parser.add_argument("--comparison-cases", default=str(DEFAULT_COMPARISON_CASES_PATH))
    parser.add_argument("--mode", choices=("replay", "pairwise", "real"), default="replay")
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--max-output-tokens", type=int, default=0)
    parser.add_argument("--max-cost-yuan", type=float, default=0.0)
    parser.add_argument("--model", default=None)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        if args.mode == "pairwise":
            report = evaluate_quality_comparison(
                cases_path=args.comparison_cases,
                max_cases=args.max_cases,
            )
        else:
            report = evaluate_quality_cases(
                cases_path=args.cases,
                mode=args.mode,
                max_cases=args.max_cases,
                max_output_tokens=args.max_output_tokens,
                max_cost_yuan=args.max_cost_yuan,
                model=args.model,
            )
    except (NotImplementedError, ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    output = (
        json.dumps(report, ensure_ascii=False, indent=2)
        if args.format == "json"
        else (
            render_quality_comparison_markdown(report)
            if args.mode == "pairwise"
            else render_quality_markdown(report)
        )
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    passed = (
        report["comparable_cases"] == report["total_cases"]
        if args.mode == "pairwise"
        else report["passed_cases"] == report["total_cases"]
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
