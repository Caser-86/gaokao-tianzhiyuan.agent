from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CURRENT_VERIFICATION = "2026-08-31-data-provenance-contract.md"
CURRENT_API_TEST_COUNT = "215"
CURRENT_WEB_TEST_COUNT = "130"
CURRENT_DOCS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "PROJECT_REVIEW.md",
    REPO_ROOT / "docs" / "interview" / "interview-qa.md",
    REPO_ROOT / "docs" / "interview" / "three-minute-demo.md",
)


def test_current_interview_docs_share_latest_verification_baseline() -> None:
    for path in CURRENT_DOCS:
        content = path.read_text(encoding="utf-8")

        assert CURRENT_API_TEST_COUNT in content
        assert CURRENT_WEB_TEST_COUNT in content
        assert CURRENT_VERIFICATION in content
