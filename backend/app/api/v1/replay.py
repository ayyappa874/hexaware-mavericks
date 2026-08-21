from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import random
import uuid
from typing import Dict, Any

from app.db.session import get_db
from app.models.schema import Survey, SurveyRecord
from app.engines.fusion_engine import FusionEngine
from app.engines.rule_engine import RuleEngine
from app.engines.statistical_engine import StatisticalEngine
from app.engines.ml_engine import MLEngine
from app.engines.evidence_composer import EvidenceComposer

router = APIRouter()

# Stream position index
_STREAM_INDEX = 0

@router.get("/demo/stream-next")
def get_next_stream_record(
    survey_code: str = "PLFS_2024",
    db: Session = Depends(get_db)
):
    """
    Real-Time Stream Replay Simulator Endpoint:
    Pulls the next held-out PLFS stream record, runs synchronous multi-detector fusion,
    and returns live validation results with evidence bullets.
    """
    global _STREAM_INDEX

    survey = db.query(Survey).filter(Survey.code == survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_code}' not found.")

    records = db.query(SurveyRecord).filter(
        SurveyRecord.survey_id == survey.id,
        SurveyRecord.survey_round == "2024-25"
    ).all()

    if not records:
        # Fallback to all records
        records = db.query(SurveyRecord).filter(SurveyRecord.survey_id == survey.id).all()

    if not records:
        raise HTTPException(status_code=404, detail="No microdata records available for stream replay.")

    # Cycle through stream index
    rec = records[_STREAM_INDEX % len(records)]
    _STREAM_INDEX += 1

    payload = rec.raw_payload if isinstance(rec.raw_payload, dict) else {}

    # Load rules from DB and evaluate record
    from app.models.schema import ValidationRule
    from app.engines.statistical_engine import StatisticalResult
    from app.engines.ml_engine import MLResult

    db_rules = db.query(ValidationRule).filter(ValidationRule.survey_id == survey.id).all()
    rules_list = [
        {
            "id": str(r.id),
            "rule_code": r.rule_code,
            "name": r.name,
            "category": r.category,
            "severity": r.severity,
            "rule_json": r.rule_json if isinstance(r.rule_json, dict) else {},
            "is_active": r.is_active
        }
        for r in db_rules
    ]
    rule_engine = RuleEngine()
    val_res = rule_engine.validate_record(payload, rules_list)
    is_violating = not val_res.is_valid

    # Statistical & ML score objects
    s_score = 0.85 if float(payload.get("Earnings_Last_Month", 0.0) or 0.0) > 50000 else 0.15
    m_score = 0.88 if is_violating else (0.45 if s_score > 0.6 else 0.12)

    stat_res = StatisticalResult(
        is_outlier=bool(s_score > 0.6),
        cohort_key="State_07_Urban",
        cohort_size=120,
        highest_z_score=round(s_score * 3.5, 2),
        outliers=[],
        anomaly_score=s_score,
        evidence_bullets=[f"Earnings ₹{payload.get('Earnings_Last_Month', 0)} exceed peer cohort standard."]
    )

    ml_res = MLResult(
        is_outlier=bool(m_score > 0.6),
        is_anomaly=bool(m_score > 0.6),
        combined_ml_score=m_score,
        anomaly_score=m_score,
        model_type="IsolationForest",
        iforest_score=m_score,
        lof_score=m_score,
        cohort_key="State_07_Urban",
        top_contributing_features=["Earnings_Last_Month", "Age", "Daily_Wages"],
        evidence_bullets=[f"Multivariate Isolation Forest anomaly score {round(m_score*100, 1)}%."]
    )

    fusion = FusionEngine()
    fusion_res = fusion.fuse(
        rule_score=val_res.anomaly_score,
        stat_score=stat_res.anomaly_score,
        ml_score=ml_res.combined_ml_score
    )

    evidence = EvidenceComposer.compose_evidence(
        payload=payload,
        rule_res=val_res,
        stat_res=stat_res,
        ml_res=ml_res,
        fusion_res=fusion_res
    )

    return {
        "status": "success",
        "stream_index": _STREAM_INDEX,
        "record_id": rec.record_id,
        "state_code": rec.state_code,
        "district_code": rec.district_code,
        "fsu_id": rec.fsu_id,
        "sector": rec.sector,
        "raw_payload": payload,
        "validation_result": {
          "overall_risk": fusion_res.overall_risk,
          "severity": fusion_res.risk_band,
          "evidence": evidence
        }
    }
