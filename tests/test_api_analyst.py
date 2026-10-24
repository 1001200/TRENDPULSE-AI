from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_sample_healthcare():
    response = client.post("/api/v1/analyst/analyze?sample_id=healthcare")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["metadata"]["rows_cleaned"] == 350
    assert "analysis_id" in data
    assert len(data["dashboard"]["kpi_cards"]) > 0
    print("[API SUCCESS] Healthcare sample returned status 200 with analysis_id:", data["analysis_id"])

    # Test download of cleaned file
    analysis_id = data["analysis_id"]
    dl_response = client.get(f"/api/v1/analyst/download-cleaned/{analysis_id}")
    assert dl_response.status_code == 200
    assert "cleaned_sample_healthcare_clinic.csv" in dl_response.headers.get("content-disposition", "")
    print("[API SUCCESS] Cleaned CSV download verified!")

def test_api_sample_marketing():
    response = client.post("/api/v1/analyst/analyze?sample_id=marketing")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["metadata"]["rows_cleaned"] == 280
    print("[API SUCCESS] Marketing sample returned status 200 with", data["metadata"]["rows_cleaned"], "rows")

if __name__ == "__main__":
    test_api_sample_healthcare()
    test_api_sample_marketing()
