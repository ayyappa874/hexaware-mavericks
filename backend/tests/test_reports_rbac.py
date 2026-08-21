import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_login():
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123password", "role": "Admin"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "Admin"

def test_reports_export_html_and_excel():
    # Test HTML export
    res_html = client.get("/api/v1/reports/export?format=html&survey_code=PLFS_2024")
    assert res_html.status_code == 200
    assert "MoSPI SURVEY SENTINEL" in res_html.text

    # Test Excel/CSV export
    res_excel = client.get("/api/v1/reports/export?format=excel&survey_code=PLFS_2024")
    assert res_excel.status_code == 200
    assert "ANOMALY FLAGS REPORT" in res_excel.text

def test_rbac_admin_rule_creation():
    import uuid
    code = f"RULE_RBAC_{uuid.uuid4().hex[:6]}"
    rule_data = {
        "survey_code": "PLFS_2024",
        "rule_code": code,
        "name": "RBAC Rule Test",
        "category": "range_check",
        "severity": "HIGH",
        "rule_json": {"field": "Age", "min": 0, "max": 110}
    }

    # 1. Viewer Role attempt -> should return 403 Forbidden
    res_viewer = client.post("/api/v1/rules", json=rule_data, headers={"X-Role": "Viewer"})
    assert res_viewer.status_code == 403

    # 2. Admin Role attempt -> should return 200 OK
    res_admin = client.post("/api/v1/rules", json=rule_data, headers={"X-Role": "Admin"})
    assert res_admin.status_code == 200
    assert res_admin.json()["status"] == "success"
