from pathlib import Path

from app.scripts import seed_catalog


def test_seed_catalog_uses_repository_root_data_directory() -> None:
    expected_data_dir = Path(__file__).resolve().parents[3] / "data"

    assert expected_data_dir == seed_catalog.DATA_DIR
