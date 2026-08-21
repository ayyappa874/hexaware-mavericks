import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_anomaly_clusters_endpoint():
    response = client.get("/api/v1/clusters")
    assert response.status_code == 200
    data = response.json()
    assert "total_clusters" in data
    assert "clusters" in data
    assert isinstance(data["clusters"], list)
