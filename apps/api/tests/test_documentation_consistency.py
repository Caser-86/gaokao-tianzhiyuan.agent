import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VERIFICATION_INDEX = REPO_ROOT / "docs" / "verification" / "latest.json"
CURRENT_DOCS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "PROJECT_REVIEW.md",
    REPO_ROOT / "docs" / "interview" / "interview-qa.md",
    REPO_ROOT / "docs" / "interview" / "three-minute-demo.md",
)


def test_current_interview_docs_share_latest_verification_baseline() -> None:
    latest = json.loads(VERIFICATION_INDEX.read_text(encoding="utf-8"))
    current_verification = latest["report"]
    current_api_test_count = str(latest["results"]["api_tests_passed"])
    current_web_test_count = str(latest["results"]["web_tests_passed"])

    for path in CURRENT_DOCS:
        content = path.read_text(encoding="utf-8")

        assert "latest.json" in content
        assert current_api_test_count in content
        assert current_web_test_count in content
        assert current_verification in content

    readme_content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert (
        f"- 前端：28 个测试模块，另有 1 个 `setup.ts`；当前收集并通过 "
        f"{current_web_test_count} 个 `test/it` 用例。"
    ) in readme_content
