import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import init_sync_db

# Initialize sync db for synchronous test client
init_sync_db()

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["mode"] == "privacy_preserving_local"
    assert data["external_llm_required"] is False

def test_sample_project_info():
    response = client.get("/api/sample-project")
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert "sample_java_project" in data["sample_path"]

def test_scan_invalid_path():
    response = client.post("/api/scan", json={"repo_path": "invalid_path_random_123"})
    assert response.status_code == 400
    assert "Directory does not exist" in response.json()["detail"]

def test_scan_sample_project():
    sample_dir = str(Path(__file__).parent.parent / "sample_java_project")
    response = client.post("/api/scan", json={"repo_path": sample_dir})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["total_files_discovered"] >= 5
    assert data["counts_by_type"]["JAVA"] >= 3
    assert data["counts_by_type"]["MAVEN_POM"] == 1

def test_analyze_and_report_lifecycle():
    sample_dir = str(Path(__file__).parent.parent / "sample_java_project")
    # 1. Run analysis
    res_analyze = client.post("/api/analyze", json={"repo_path": sample_dir, "enable_semantic": True})
    assert res_analyze.status_code == 200
    data = res_analyze.json()
    analysis_id = data["analysis_id"]
    assert analysis_id is not None
    assert data["summary"]["total_files"] >= 5
    assert data["summary"]["contradictory"] >= 1
    assert data["summary"]["consistent"] >= 1
    assert len(data["findings"]) > 0

    # 2. Get history
    res_hist = client.get("/api/history")
    assert res_hist.status_code == 200
    history_list = res_hist.json()
    assert any(h["id"] == analysis_id for h in history_list)

    # 3. Retrieve report by ID
    res_report = client.get(f"/api/reports/{analysis_id}")
    assert res_report.status_code == 200
    report_data = res_report.json()
    assert report_data["analysis_id"] == analysis_id

    # 4. Export JSON
    res_json = client.get(f"/api/reports/{analysis_id}/export?format=json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers["content-type"]

    # 5. Export CSV
    res_csv = client.get(f"/api/reports/{analysis_id}/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "classification" in res_csv.text

    # 6. Export HTML
    res_html = client.get(f"/api/reports/{analysis_id}/export?format=html")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "<!DOCTYPE html>" in res_html.text

def test_evaluate_endpoint():
    response = client.post("/api/evaluate?enable_semantic=true")
    assert response.status_code == 200
    data = response.json()
    assert data["precision"] > 0.8
    assert data["f1_score"] > 0.7
    assert len(data["case_breakdown"]) == 6
