import httpx
import time

API_BASE = "http://localhost:8005/api/v1"

def test_flow():
    print("=== 1. Testing Model Lab Training & Held-Out Evaluation ===")
    train_input = {
        "survey_code": "PLFS_2024",
        "model_name": "PLFS_IsolationForest_Champion_v1",
        "algorithm": "ISOLATION_FOREST",
        "hyperparameters": {"n_estimators": 100, "contamination": 0.05},
        "train_round": "2023-24",
        "test_round": "2024-25"
    }

    r_train = httpx.post(f"{API_BASE}/models/train", json=train_input, timeout=30.0)
    assert r_train.status_code == 200
    res_train = r_train.json()

    print("Model Training & Evaluation Result:")
    model_info = res_train["model"]
    print("Model ID:", model_info["id"])
    print("Model Version:", model_info["version"])
    print("Algorithm:", model_info["algorithm"])
    metrics = model_info["metrics"]
    print(f"Metrics -> Precision: {metrics['precision']}, Recall: {metrics['recall']}, F1: {metrics['f1_score']}, ROC AUC: {metrics['roc_auc']}")
    print(f"Dataset -> Train Samples (2023-24): {metrics['train_samples']}, Test Samples (2024-25): {metrics['test_samples']}")

    assert metrics["f1_score"] > 0.0

    print("\n=== 2. Testing Model Comparison Registry ===")
    r_models = httpx.get(f"{API_BASE}/models", timeout=30.0)
    assert r_models.status_code == 200
    models_list = r_models.json()
    print(f"Total Trained Models in Registry: {len(models_list)}")
    assert len(models_list) >= 1

    print("\n=== 3. Testing Champion Model Promotion ===")
    model_id = model_info["id"]
    r_promote = httpx.post(f"{API_BASE}/models/{model_id}/promote", timeout=30.0)
    assert r_promote.status_code == 200
    res_promote = r_promote.json()
    print(f"Promoted Model: {res_promote['champion_model']['model_name']} ({res_promote['champion_model']['version']}) | Active Champion: {res_promote['champion_model']['is_active']}")
    assert res_promote["champion_model"]["is_active"] is True

    print("\n=== 4. Testing Supervisor Feedback Submission ===")
    r_flags = httpx.get(f"{API_BASE}/flags", timeout=30.0)
    assert r_flags.status_code == 200
    flags = r_flags.json()["flags"]
    assert len(flags) >= 2

    # Submit CONFIRMED feedback on flag 0
    flag_0_id = flags[0]["id"]
    r_fb1 = httpx.post(
        f"{API_BASE}/flags/{flag_0_id}/feedback",
        json={"supervisor_id": "SUPERVISOR_01", "decision": "CONFIRMED", "comments": "Verified child salaried employment anomaly against physical schedule."},
        timeout=30.0
    )
    assert r_fb1.status_code == 200
    print(f"Submitted CONFIRMED decision for flag {flag_0_id}: Status={r_fb1.json()['flag_status']}")

    # Submit DISMISSED feedback on flag 1
    flag_1_id = flags[1]["id"]
    r_fb2 = httpx.post(
        f"{API_BASE}/flags/{flag_1_id}/feedback",
        json={"supervisor_id": "SUPERVISOR_02", "decision": "DISMISSED", "comments": "Confirmed high wage due to specialized IT consultancy role in urban sector."},
        timeout=30.0
    )
    assert r_fb2.status_code == 200
    print(f"Submitted DISMISSED decision for flag {flag_1_id}: Status={r_fb2.json()['flag_status']}")

    print("\n=== 5. Testing Active Learning Fusion Weight Recalibration ===")
    r_calib = httpx.post(f"{API_BASE}/fusion/calibrate", timeout=30.0)
    assert r_calib.status_code == 200
    res_calib = r_calib.json()
    print("Recalibration Result:")
    print("Status:", res_calib["status"])
    print("Recalibrated Fusion Weights:", res_calib["new_weights"])
    print("Detector Precision Estimates:", res_calib["detector_precisions"])

    print("\nALL MODEL LAB AND SUPERVISOR FEEDBACK LOOP TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_flow()
