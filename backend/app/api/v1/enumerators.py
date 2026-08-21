from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.models.schema import Survey, EnumeratorFingerprint
from app.engines.enumerator_engine import EnumeratorEngine

router = APIRouter()

@router.get("/enumerators/ranked")
def get_ranked_enumerators(
    survey_code: str = "PLFS_2024",
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all enumerators/FSUs sorted by composite risk score (highest risk first).
    """
    survey = db.query(Survey).filter(Survey.code == survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_code}' not found.")

    # Check if fingerprints exist, otherwise compute automatically
    count = db.query(EnumeratorFingerprint).filter(EnumeratorFingerprint.survey_id == survey.id).count()
    if count == 0:
        EnumeratorEngine.compute_and_store_fingerprints(db, survey.id)

    query = db.query(EnumeratorFingerprint).filter(EnumeratorFingerprint.survey_id == survey.id)
    total_count = query.count()
    fps = query.order_by(EnumeratorFingerprint.composite_risk_score.desc()).offset(offset).limit(limit).all()

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "enumerators": [
            {
                "id": fp.id,
                "enumerator_id": fp.enumerator_id, # FSU Code
                "total_records": fp.total_records,
                "missing_rate": fp.missing_rate,
                "digit_preference_score": fp.digit_preference_score,
                "historical_anomaly_rate": fp.historical_anomaly_rate,
                "composite_risk_score": fp.composite_risk_score,
                "metrics": fp.metrics_json,
                "updated_at": fp.updated_at
            }
            for fp in fps
        ]
    }

@router.get("/enumerators/{enumerator_id}/fingerprint")
def get_enumerator_fingerprint(
    enumerator_id: str,
    survey_code: str = "PLFS_2024",
    db: Session = Depends(get_db)
):
    """
    Get detailed fingerprint metrics and risk breakdown for a specific enumerator/FSU ID.
    """
    survey = db.query(Survey).filter(Survey.code == survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_code}' not found.")

    fp = db.query(EnumeratorFingerprint).filter(
        EnumeratorFingerprint.survey_id == survey.id,
        EnumeratorFingerprint.enumerator_id == enumerator_id
    ).first()

    if not fp:
        # Re-compute if needed
        EnumeratorEngine.compute_and_store_fingerprints(db, survey.id)
        fp = db.query(EnumeratorFingerprint).filter(
            EnumeratorFingerprint.survey_id == survey.id,
            EnumeratorFingerprint.enumerator_id == enumerator_id
        ).first()

    if not fp:
        raise HTTPException(status_code=404, detail=f"Enumerator/FSU '{enumerator_id}' not found.")

    return {
        "id": fp.id,
        "enumerator_id": fp.enumerator_id,
        "total_records": fp.total_records,
        "missing_rate": fp.missing_rate,
        "digit_preference_score": fp.digit_preference_score,
        "historical_anomaly_rate": fp.historical_anomaly_rate,
        "composite_risk_score": fp.composite_risk_score,
        "metrics": fp.metrics_json,
        "updated_at": fp.updated_at
    }
