import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "verify-data-assets.py"
spec = importlib.util.spec_from_file_location("verify_data_assets", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise AssertionError(f"Unable to load {SCRIPT_PATH}")
verify_data_assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_data_assets)


class VerifyDataAssetsTests(unittest.TestCase):
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
