import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.engines.rule_engine import RuleEngine, ValidationResult
from app.engines.statistical_engine import StatisticalEngine, StatisticalResult
from app.engines.ml_engine import MLEngine, MLResult
from app.engines.fusion_engine import FusionEngine, FusionResult
from app.engines.evidence_composer import EvidenceComposer

@pytest.fixture
def baseline_sample():
    # Generate 50 realistic baseline records for State 09, Sector 1
    recs = []
    for i in range(50):
        recs.append({
            "State": "09",
            "Sector": "1",
            "Age": 30 + (i % 10),
            "Usual_Principal_Activity_Status": 31,
            "Earnings_Last_Month": 20000.0 + (i * 200),
            "Daily_Wages": 750.0 + (i * 5),
            "Monthly_Exp": 15000.0 + (i * 100),
            "General_Edu": 10,
            "Multiplier": 450.0
        })
    return recs

def test_statistical_engine_cohort_scoring(baseline_sample):
    engine = StatisticalEngine()
    engine.fit(baseline_sample)

    # Test normal record in cohort
    normal_rec = {
        "State": "09",
        "Sector": "1",
        "Age": 32,
        "Usual_Principal_Activity_Status": 31,
        "Earnings_Last_Month": 22000.0,
        "Daily_Wages": 800.0,
        "Monthly_Exp": 16000.0
    }
    res_normal = engine.evaluate_record(normal_rec)
    assert res_normal.anomaly_score < 0.50
    assert len(res_normal.outliers) == 0

    # Test extreme earnings outlier in cohort
    outlier_rec = {
        "State": "09",
        "Sector": "1",
        "Age": 35,
        "Usual_Principal_Activity_Status": 31,
        "Earnings_Last_Month": 250000.0, # 10x cohort median
        "Daily_Wages": 9000.0,
        "Monthly_Exp": 120000.0
    }
    res_outlier = engine.evaluate_record(outlier_rec)
    assert res_outlier.anomaly_score > 0.50
    assert len(res_outlier.outliers) >= 1
    assert "Earnings_Last_Month" in [o.field for o in res_outlier.outliers]

def test_ml_engine_iforest_and_lof(baseline_sample):
    engine = MLEngine()
    engine.fit(baseline_sample)

    # Extreme multivariate anomaly
    anomalous_rec = {
        "State": "09",
        "Sector": "1",
        "Age": 35,
        "Usual_Principal_Activity_Status": 31,
        "Earnings_Last_Month": 999999.0,
        "Daily_Wages": 99999.0,
        "Monthly_Exp": 500000.0,
        "General_Edu": 1,
        "Multiplier": 10.0
    }

    res = engine.evaluate_record(anomalous_rec)
    assert res.combined_ml_score > 0.40
    assert len(res.top_contributing_features) > 0

def test_fusion_engine_risk_bands():
    fusion = FusionEngine(w_rule=0.35, w_stat=0.35, w_ml=0.30)

    # Normal score
    res_low = fusion.fuse(rule_score=0.0, stat_score=0.1, ml_score=0.1)
    assert res_low.risk_band == "NORMAL"
    assert res_low.overall_risk <= 25

    # High priority anomaly score
    res_high = fusion.fuse(rule_score=0.8, stat_score=0.8, ml_score=0.8)
    assert res_high.risk_band == "HIGH_PRIORITY"
    assert res_high.overall_risk >= 76
    assert res_high.agreement_count == 3

def test_evidence_composer():
    rule_engine = RuleEngine()
    stat_engine = StatisticalEngine()
    ml_engine = MLEngine()
    fusion_engine = FusionEngine()

    baseline = [{
        "State": "27", "Sector": "2", "Age": 28, "Usual_Principal_Activity_Status": 31,
        "Earnings_Last_Month": 30000.0, "Daily_Wages": 1100.0, "Monthly_Exp": 22000.0
    }] * 20
    stat_engine.fit(baseline)
    ml_engine.fit(baseline)

    payload = {
        "State": "27",
        "Sector": "2",
        "Age": 28,
        "Usual_Principal_Activity_Status": 31, # Rule violation condition test
        "Earnings_Last_Month": 500000.0, # Stat outlier
        "Daily_Wages": 15000.0,
        "Monthly_Exp": 200000.0,
        "Person_No": 1,
        "Rel_To_Head": 1,
        "FSU": "FSU27001"
    }

    rule_res = rule_engine.validate_record(payload, [{
        "rule_code": "R1", "name": "Child Salaried Check", "category": "logical_consistency",
        "severity": "CRITICAL", "is_active": True,
        "rule_json": {"condition": {"field": "Usual_Principal_Activity_Status", "operator": "equals", "value": 31}, "assertion": {"field": "Age", "operator": "gte", "value": 15}}
    }])

    stat_res = stat_engine.evaluate_record(payload)
    ml_res = ml_engine.evaluate_record(payload)
    fusion_res = fusion_engine.fuse(rule_res.anomaly_score, stat_res.anomaly_score, ml_res.combined_ml_score)

    evidence = EvidenceComposer.compose_evidence(payload, rule_res, stat_res, ml_res, fusion_res)

    assert "overall_risk" in evidence
    assert "narrative_bullets" in evidence
    assert 3 <= len(evidence["narrative_bullets"]) <= 5
    assert len(evidence["detectors_fired"]) >= 1
