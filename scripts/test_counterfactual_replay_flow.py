import httpx

API_BASE = "http://localhost:8005/api/v1"

def test_flow():
    print("=== 1. Testing Counterfactual Explanation API ===")
    r_flags = httpx.get(f"{API_BASE}/flags?limit=1", timeout=30.0)
    assert r_flags.status_code == 200
    flag = r_flags.json()["flags"][0]
    rec_id = flag["record_id"]

    r_cf = httpx.get(f"{API_BASE}/records/{rec_id}/counterfactual", timeout=30.0)
    assert r_cf.status_code == 200
    cf_res = r_cf.json()

    print(f"Record ID: {cf_res['record_id']}")
    print(f"Original Risk: {cf_res['original_risk_score']} -> Projected Risk: {cf_res['projected_counterfactual_risk_score']} (Reduction: -{cf_res['risk_reduction']})")
    print("Recommendations:")
    for rec in cf_res["recommendations"]:
        print(f"  - Field '{rec['field']}': {rec['current_value']} -> {rec['target_value']} | Delta: {rec['delta']}")

    assert len(cf_res["recommendations"]) >= 1

    print("\n=== 2. Testing Real-Time Stream Replay API ===")
    for i in range(3):
        r_stream = httpx.get(f"{API_BASE}/demo/stream-next", timeout=30.0)
        assert r_stream.status_code == 200
        st_data = r_stream.json()
        v = st_data["validation_result"]
        print(f"Stream Step #{st_data['stream_index']}: Record {st_data['record_id']} | Risk Score: {v['overall_risk']} ({v['severity']})")

    print("\nALL COUNTERFACTUAL AND STREAM REPLAY FLOW TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_flow()
