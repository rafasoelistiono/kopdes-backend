from fastapi.testclient import TestClient

from app.main import app


def test_komi_agent_smoke():
    client = TestClient(app)
    body = {
        "message": "kenapa koperasi ini tidak sehat dan apa prioritasnya?",
        "page": "/dashboard/pengurus-koperasi",
        "dashboard_key": "pengurus-koperasi",
        "role": "pengurus_koperasi",
        "koperasi_ref": "KOP-0008016CB39E",
        "kode_wilayah": "36.72.06.1001",
        "period": "2026-07",
        "mode": "analysis",
        "use_llm": False,
    }
    response = client.post("/api/komi/agent", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert "mode" in payload
    assert "intent" in payload
    assert "health_score" in payload
    assert "correlations" in payload
    assert isinstance(payload["correlations"], list)
    assert "recommended_actions" in payload
    assert "citations" in payload
    assert "sources" in payload
    assert "safety" in payload
    assert payload["safety"]["pii_redacted"] is True
    assert payload["safety"]["scope_checked"] is True
    assert payload["llm_used"] is False


def test_komi_agent_v1_route():
    client = TestClient(app)
    body = {
        "message": "analisis kesehatan koperasi",
        "page": "/dashboard/satgas-kdmp",
        "dashboard_key": "satgas-kdmp",
        "role": "satgas_kdmp",
        "scope_level": "nasional",
        "scope_code": "nasional",
        "period": "2026-07",
        "mode": "analysis",
        "use_llm": False,
    }
    response = client.post("/api/v1/komi/agent", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert "correlations" in payload
    assert "safety" in payload


def test_komi_agent_has_correlations():
    client = TestClient(app)
    body = {
        "message": "apa saja masalah di koperasi ini?",
        "page": "/dashboard/pengurus-koperasi",
        "dashboard_key": "pengurus-koperasi",
        "role": "pengurus_koperasi",
        "koperasi_ref": "KOP-0008016CB39E",
        "kode_wilayah": "36.72.06.1001",
        "period": "2026-07",
        "use_llm": False,
    }
    response = client.post("/api/komi/agent", json=body)
    assert response.status_code == 200
    payload = response.json()
    correlations = payload["correlations"]
    for corr in correlations:
        assert "key" in corr
        assert "title" in corr
        assert "evidence" in corr
        assert "meaning" in corr
        assert "severity" in corr
        assert corr["severity"] in {"success", "warning", "danger", "neutral"}
        assert "sources" in corr


def test_komi_agent_safety_fields():
    client = TestClient(app)
    body = {
        "message": "health score berapa?",
        "page": "/dashboard/pengurus-koperasi",
        "dashboard_key": "pengurus-koperasi",
        "role": "pengurus_koperasi",
        "koperasi_ref": "KOP-0008016CB39E",
        "kode_wilayah": "36.72.06.1001",
        "period": "2026-07",
        "use_llm": False,
    }
    response = client.post("/api/komi/agent", json=body)
    payload = response.json()
    safety = payload["safety"]
    assert safety["pii_redacted"] is True
    assert safety["scope_checked"] is True
    assert isinstance(safety["grounded"], bool)


def test_komi_export_belum_rat():
    client = TestClient(app)
    body = {
        "message": "buatkan CSV koperasi yang belum RAT",
        "dashboard_key": "satgas-kdmp",
        "role": "satgas_kdmp",
        "scope_level": "nasional",
        "scope_code": "nasional",
        "period": "2026-07",
        "format": "csv",
        "limit": 100,
    }
    response = client.post("/api/komi/export", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["intent"] == "export_belum_rat"
    assert "filename" in payload
    assert payload["content_type"] == "text/csv"
    assert "csv" in payload
    assert isinstance(payload["row_count"], int)
    assert isinstance(payload["columns"], list)
    assert "safety" in payload
    assert payload["safety"]["pii_redacted"] is True
    assert "nik" not in payload["columns"]
    assert "email" not in payload["columns"]
    assert "no_hp" not in payload["columns"]
    assert "alamat" not in payload["columns"]
    assert "rekening" not in payload["columns"]


def test_komi_export_v1_route():
    client = TestClient(app)
    body = {
        "message": "export produk lambat",
        "koperasi_ref": "KOP-0008016CB39E",
        "period": "2026-07",
    }
    response = client.post("/api/v1/komi/export", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["intent"] == "export_produk_lambat"


def test_komi_export_unknown_returns_safe_error():
    client = TestClient(app)
    body = {
        "message": "buatkan data yang aneh sekali",
        "period": "2026-07",
    }
    response = client.post("/api/komi/export", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert "error" in payload
    assert "safety" in payload


def test_komi_export_no_sensitive_columns():
    client = TestClient(app)
    body = {
        "message": "export pengurus",
        "koperasi_ref": "KOP-0008016CB39E",
        "period": "2026-07",
    }
    response = client.post("/api/komi/export", json=body)
    payload = response.json()
    columns = payload.get("columns", [])
    sensitive = {"nik", "ktp", "email", "no_hp", "alamat", "rekening", "file_ktp", "foto_profil"}
    assert not sensitive.intersection(set(columns))


def test_komi_export_simpanan_unpaid():
    client = TestClient(app)
    body = {
        "message": "download simpanan unpaid",
        "koperasi_ref": "KOP-0008016CB39E",
        "period": "2026-07",
    }
    response = client.post("/api/komi/export", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["intent"] == "export_simpanan_unpaid"


def test_komi_export_potensi_desa():
    client = TestClient(app)
    body = {
        "message": "export potensi desa",
        "kode_wilayah": "36.72.06.1001",
        "period": "2026-07",
    }
    response = client.post("/api/komi/export", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["intent"] == "export_potensi_desa"
