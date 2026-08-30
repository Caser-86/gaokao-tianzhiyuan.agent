import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "verify-data-assets.py"
spec = importlib.util.spec_from_file_location("verify_data_assets", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise AssertionError(f"Unable to load {SCRIPT_PATH}")
verify_data_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_data_assets)


def _empty_featured_payload() -> dict:
    return {
        "schools": [],
        "majors": [],
        "rotation": {
            "schools": {"enabled": False, "frequency_days": 1, "window_size": 1, "ordered_slugs": []},
            "majors": {"enabled": False, "frequency_days": 1, "window_size": 1, "ordered_slugs": []},
        },
    }


class VerifyDataAssetsTests(unittest.TestCase):
    def test_rejects_catalog_without_data_provenance(self) -> None:
        catalog = {
            "search_entry": {"title": "入口", "description": "说明", "quick_prompts": []},
            "schools": [],
            "majors": [],
        }

        with self.assertRaises(verify_data_assets.DataAssetValidationError) as context:
            verify_data_assets.validate_data(catalog, _empty_featured_payload())

        self.assertIn("data_provenance", str(context.exception))

    def test_accepts_demo_data_provenance_contract(self) -> None:
        catalog = {
            "data_provenance": {
                "status": "demo",
                "source_name": "项目手工编写演示数据",
                "source_url": None,
                "updated_at": "2026-08-30",
                "applicable_year": None,
                "region": "多地区示例",
                "official": False,
                "disclaimer": "仅用于功能演示，不构成招生、排名或志愿决策依据。",
            },
            "search_entry": {"title": "入口", "description": "说明", "quick_prompts": []},
            "schools": [],
            "majors": [],
        }

        verify_data_assets.validate_data(
            catalog,
            _empty_featured_payload(),
        )

    def test_rejects_non_demo_provenance_without_source_and_year(self) -> None:
        catalog = {
            "data_provenance": {
                "status": "official",
                "source_name": "官方数据",
                "source_url": None,
                "updated_at": "2026-08-30",
                "applicable_year": None,
                "region": "江苏",
                "official": True,
                "disclaimer": "待审核。",
            },
            "search_entry": {"title": "入口", "description": "说明", "quick_prompts": []},
            "schools": [],
            "majors": [],
        }

        with self.assertRaises(verify_data_assets.DataAssetValidationError) as context:
            verify_data_assets.validate_data(catalog, _empty_featured_payload())

        self.assertIn("source_url", str(context.exception))
        self.assertIn("applicable_year", str(context.exception))

    def test_rejects_school_relation_to_unknown_major_slug(self) -> None:
        catalog = {
            "search_entry": {"title": "入口", "description": "说明", "quick_prompts": []},
            "schools": [
                {
                    "slug": "school-a",
                    "name": "学校 A",
                    "region": "地区",
                    "city": "城市",
                    "related_majors": ["missing-major"],
                }
            ],
            "majors": [],
        }

        with self.assertRaises(verify_data_assets.DataAssetValidationError) as context:
            verify_data_assets.validate_data(catalog, {"schools": [], "majors": [], "rotation": {}})

        self.assertIn("missing-major", str(context.exception))


if __name__ == "__main__":
    unittest.main()
