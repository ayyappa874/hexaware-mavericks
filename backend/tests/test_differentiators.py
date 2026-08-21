import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.engines.benford_engine import BenfordEngine
from app.engines.privacy_engine import DifferentialPrivacyEngine
from app.engines.causal_engine import CausalAttributionEngine

client = TestClient(app)

def test_benford_engine_analysis():
    # Generate list matching Benford's distribution
    values = [100.0, 150.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0] * 10
    res = BenfordEngine.analyze_digits(values)
    assert "chi_square_stat" in res
    assert "digit_counts" in res
    assert res["total_samples"] == 100

def test_benford_fdr_correction():
    p_vals = [0.001, 0.01, 0.04, 0.20, 0.50]
    sig = BenfordEngine.apply_fdr_correction(p_vals, alpha=0.05)
    assert len(sig) == 5
    assert sig[0] is True # 0.001 significant

def test_audit_verify_chain_endpoint():
    res = client.get("/api/v1/audit/verify-chain")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VERIFIED"
    assert data["chain_valid"] is True

def test_canary_detection_rate_endpoint():
    res = client.get("/api/v1/canary/detection-rate")
    assert res.status_code == 200
    data = res.json()
    assert "canary_detection_rate" in data
    assert data["canary_detection_rate"] > 80.0

def test_differential_privacy_engine():
    stats = {"total_records": 1000, "high_priority_count": 12, "mean_risk_score": 24.5}
    sanitized = DifferentialPrivacyEngine.sanitize_aggregates(stats, privacy_budget="medium")
    assert "_privacy_meta" in sanitized
    assert sanitized["_privacy_meta"]["epsilon"] == 1.0

def test_causal_attribution_engine():
    res = CausalAttributionEngine.attribute_drift(state_code="07", indicator="LFPR", delta=-2.5, z_score=-3.1)
    assert "most_likely_explanation" in res
    assert len(res["hypotheses"]) == 3
