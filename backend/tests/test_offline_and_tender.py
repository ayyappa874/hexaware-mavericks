import sys
import os
import subprocess
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_p2p_hotspot_ingest_endpoint():
    payload = {
        "device_id": "CAPI_TABLET_FIELD_07",
        "survey_code": "PLFS_2024",
        "records": [
            {
                "id": "REC_P2P_001",
                "Age": 28,
                "Sex": 1,
                "Usual_Principal_Activity_Status": 31,
                "Earnings_Last_Month": 45000.0
            }
        ]
    }

    res = client.post("/api/v1/p2p/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["mode"] == "LOCAL_HOTSPOT_P2P"
    assert data["records_received"] == 1

def test_standalone_offline_validator_script():
    # Run offline_validator_cli.py against mock CSV
    test_csv_path = os.path.abspath("scripts/test_batch_plfs.csv")
    if os.path.exists(test_csv_path):
        res = subprocess.run(
            [sys.executable, "scripts/offline_validator_cli.py", "--input", test_csv_path, "--output", "scratch/test_offline_out.json"],
            capture_output=True,
            text=True
        )
        assert res.returncode == 0
        assert "Validation complete!" in res.stdout
