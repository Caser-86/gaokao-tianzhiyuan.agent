from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CURRENT_VERIFICATION = "2026-08-30-evaluation-and-data-trust.md"
CURRENT_DOCS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "PROJECT_REVIEW.md",
    REPO_ROOT / "docs" / "interview" / "interview-qa.md",
    REPO_ROOT / "docs" / "interview" / "three-minute-demo.md",
)


def test_current_interview_docs_share_latest_verification_baseline() -> None:
    for path in CURRENT_DOCS:
        content = path.read_text(encoding="utf-8")

        assert "213" in content
        assert "129" in content
        assert CURRENT_VERIFICATION in content
