from fastapi.testclient import TestClient

from app.main import app
from app.repositories.lookup_repository import get_koperasi_options, get_wilayah_options


def test_core_dashboard_endpoints_smoke():
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/meta/tables").status_code == 200

    koperasi_ref = get_koperasi_options(limit=1)[0]["koperasi_ref"]
    kode_wilayah = get_wilayah_options()[0]["kode_wilayah"]

    checks = [
        f"/api/v1/dashboards/pengurus-koperasi?koperasi_ref={koperasi_ref}&period=2026-07",
        f"/api/v1/dashboards/kepala-desa?kode_wilayah={kode_wilayah}&period=2026-07",
        "/api/v1/dashboards/satgas-kdmp?year=2026",
    ]

    for path in checks:
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert "kpis" in payload
        assert "sections" in payload
        assert "charts" in payload
        assert "tables" in payload
        assert "metadata" in payload


def test_scope_validation():
    client = TestClient(app)

    assert client.get("/api/v1/dashboards/pengurus-koperasi").status_code == 400
    assert client.get("/api/v1/dashboards/kepala-desa").status_code == 400
    assert client.get("/api/v1/dashboards/operator-koperasi").status_code == 404
    assert client.get("/api/v1/dashboards/bank-reviewer").status_code == 404
