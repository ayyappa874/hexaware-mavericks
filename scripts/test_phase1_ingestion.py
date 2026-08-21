import httpx
import time
import os

API_BASE = "http://localhost:8005/api/v1"

def test_phase1_flow():
    print("=== 1. Testing Rule CRUD API ===")
    r_rules = httpx.get(f"{API_BASE}/rules")
    if r_rules.status_code != 200:
        print("ERROR r_rules:", r_rules.status_code, r_rules.text)
    assert r_rules.status_code == 200
    rules_data = r_rules.json()
    print(f"Active rules in DB: {len(rules_data)}")
    assert len(rules_data) >= 5

    print("\n=== 2. Testing Synchronous Streaming Ingestion API ===")
    anomalous_record = {
        "survey_code": "PLFS_2024",
        "survey_round": "2024-25",
        "state_code": "27",
        "district_code": "005",
        "sector": "2",
        "fsu_id": "FSU_STREAM_DEMO",
        "raw_payload": {
            "Survey_Round": "2024-25",
            "State": "27",
            "District": "005",
            "Sector": "2",
            "Hh_No": 12,
            "Person_No": 1,
            "Rel_To_Head": 3, # Inconsistency: Person 1 is Child
            "Sex": 1,
            "Age": 11, # Age < 15
            "General_Edu": 12, # Inconsistency: Age 11 is Graduate
            "Usual_Principal_Activity_Status": 31, # Inconsistency: Age 11 is Regular Salaried
            "Earnings_Last_Month": 85000.0,
            "Daily_Wages": 3200.0,
            "Monthly_Exp": 25000.0
        }
    }

    r_stream = httpx.post(f"{API_BASE}/records/ingest/stream", json=anomalous_record)
    assert r_stream.status_code == 200
    res_stream = r_stream.json()
    print("Stream Ingestion Result:")
    print("Is Valid:", res_stream["validation_result"]["is_valid"])
    print("Anomaly Score:", res_stream["validation_result"]["anomaly_score"])
    print("Highest Severity:", res_stream["validation_result"]["highest_severity"])
    print("Violations Bullets:", res_stream["validation_result"]["summary_bullets"])
    assert res_stream["validation_result"]["is_valid"] is False
    assert res_stream["validation_result"]["flag_id"] is not None

    print("\n=== 3. Testing Batch File Upload Ingestion API ===")
    csv_file_path = "data/plfs_microdata.csv"
    with open(csv_file_path, "rb") as f:
        files = {"file": ("plfs_microdata.csv", f, "text/csv")}
        r_batch = httpx.post(f"{API_BASE}/records/ingest/batch", files=files)
    
    assert r_batch.status_code == 200
    res_batch = r_batch.json()
    job_id = res_batch["job_id"]
    print(f"Submitted Batch Job ID: {job_id}, Status: {res_batch['status']}")

    print("\n=== 4. Polling Job Status ===")
    for _ in range(20):
        r_job = httpx.get(f"{API_BASE}/jobs/{job_id}")
        job_info = r_job.json()
        print(f"Job Status: {job_info['status']} | Processed: {job_info.get('processed_records', 0)} / {job_info.get('total_records', 0)} | Flags: {job_info.get('flag_count', 0)}")
        if job_info["status"] in ("completed", "failed"):
            break
        time.sleep(0.5)

    if job_info["status"] == "failed":
        print("JOB ERROR DETAILS:", job_info.get("error"))
    assert job_info["status"] == "completed"

    print("\n=== 5. Querying Anomaly Flags ===")
    r_flags = httpx.get(f"{API_BASE}/flags")
    assert r_flags.status_code == 200
    flags_data = r_flags.json()
    print(f"Total Anomaly Flags Created in DB: {flags_data['total']}")
    assert flags_data['total'] > 0
    
    sample_flag = flags_data['flags'][0]
    print("Sample Flag Entry:")
    print(f"Detector: {sample_flag['detector_type']} | Severity: {sample_flag['severity']} | Score: {sample_flag['score']}")
    print("Evidence Bullets:", sample_flag['evidence'].get('summary_bullets', []))

    print("\nALL PHASE 1 INGESTION AND RULE VALIDATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase1_flow()
