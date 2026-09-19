from app.services.data_provenance import get_data_provenance


def test_data_provenance_returns_demo_boundary_without_shared_mutation() -> None:
    first = get_data_provenance()
    first["status"] = "official"

    second = get_data_provenance()

    assert second["status"] == "demo"
    assert second["official"] is False
    assert second["updated_at"] == "2026-08-30"
    assert second["region"] == "多地区示例"
