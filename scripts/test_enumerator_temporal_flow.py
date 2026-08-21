import httpx
import time

API_BASE = "http://localhost:8005/api/v1"

def test_flow():
    print("=== 1. Testing Ranked Enumerators API ===")
    r_enum = httpx.get(f"{API_BASE}/enumerators/ranked", timeout=30.0)
    assert r_enum.status_code == 200
    res_enum = r_enum.json()

    print(f"Total Enumerator/FSU Profiles in DB: {res_enum['total']}")
    assert res_enum["total"] > 0

    top_fsu = res_enum["enumerators"][0]
    print("\nTop Risk Enumerator Profile:")
    print("FSU ID:", top_fsu["enumerator_id"])
    print("Total Records:", top_fsu["total_records"])
    print("Composite Risk Score:", top_fsu["composite_risk_score"])
    print("Digit Preference Score:", top_fsu["digit_preference_score"])
    print("Category Skew HHI:", top_fsu["metrics"]["category_skew"])
    print("Historical Anomaly Rate:", top_fsu["historical_anomaly_rate"])

    print("\n=== 2. Testing Specific Enumerator Fingerprint API ===")
    target_fsu_id = top_fsu["enumerator_id"]
    r_fp = httpx.get(f"{API_BASE}/enumerators/{target_fsu_id}/fingerprint", timeout=30.0)
    assert r_fp.status_code == 200
    res_fp = r_fp.json()
    print(f"Successfully retrieved fingerprint for '{target_fsu_id}' with risk score {res_fp['composite_risk_score']}.")

    print("\n=== 3. Testing Temporal Drift Dashboard API ===")
    r_drift = httpx.get(f"{API_BASE}/dashboard/temporal-drift", timeout=30.0)
    assert r_drift.status_code == 200
    res_drift = r_drift.json()

    print(f"Status: {res_drift['status']} | Baseline Round: {res_drift.get('baseline_round')} | Current Round: {res_drift.get('current_round')}")
    print(f"States Evaluated: {res_drift.get('states_evaluated', 0)}")
    print(f"Significant Drift Flags Count: {len(res_drift.get('significant_drift_flags', []))}")

    if res_drift.get("drift_analysis"):
        sample_st = res_drift["drift_analysis"][0]
        print(f"\nSample State Indicator Comparison (State {sample_st['state_code']}):")
        inds = sample_st["indicators"]
        print(f"  - LFPR: {inds['lfpr']['baseline']}% -> {inds['lfpr']['current']}% (Delta: {inds['lfpr']['delta']}%, Z: {inds['lfpr']['z_score']})")
        print(f"  - WPR:  {inds['wpr']['baseline']}% -> {inds['wpr']['current']}% (Delta: {inds['wpr']['delta']}%, Z: {inds['wpr']['z_score']})")
        print(f"  - UR:   {inds['ur']['baseline']}% -> {inds['ur']['current']}% (Delta: {inds['ur']['delta']}%, Z: {inds['ur']['z_score']})")

    print("\nALL ENUMERATOR PROFILING AND TEMPORAL DRIFT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_flow()
