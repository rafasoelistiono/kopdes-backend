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


def test_komi_insight_smoke():
    client = TestClient(app)

    response = client.post(
        "/api/komi/insight",
        json={
            "page": "/dashboard/satgas-kdmp",
            "role": "satgas_kdmp",
            "scope_level": "nasional",
            "scope_code": "nasional",
            "period": "2026-07",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "health_score" in payload
    assert "insights" in payload
    assert "recommended_actions" in payload


def test_komi_chat_smoke():
    client = TestClient(app)

    body = {
        "message": "berapa omzet dan transaksi bulan ini?",
        "page": "/dashboard/pengurus-koperasi",
        "dashboard_key": "pengurus-koperasi",
        "role": "pengurus_koperasi",
        "koperasi_ref": "KOP-0008016CB39E",
        "kode_wilayah": "36.72.06.1001",
        "period": "2026-07",
    }
    for path in ["/api/komi/chat", "/api/v1/komi/chat"]:
        response = client.post(path, json=body)
        assert response.status_code == 200
        payload = response.json()
        assert payload["intent"] == "transaksi"
        assert payload["confidence"] == "rule"
        assert "answer" in payload
        assert "rule_answer" in payload
        assert "supporting_data" in payload
        assert "recommended_actions" in payload
        assert payload["generated_by"] in {"rule", "gemini_flash_rewrite", "openrouter_rewrite"}
        assert "llm_used" in payload
