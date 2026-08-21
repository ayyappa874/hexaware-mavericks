from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.schema import AnomalyFlag, SupervisorFeedback, AuditLog
from app.engines.feedback_calibration import FeedbackCalibrationEngine

router = APIRouter()

class FeedbackSubmitInput(BaseModel):
    supervisor_id: str = "SUPERVISOR_01"
    decision: str # CONFIRMED or DISMISSED
    comments: Optional[str] = None

@router.post("/flags/{flag_id}/feedback")
def submit_supervisor_feedback(
    flag_id: str,
    data: FeedbackSubmitInput,
    db: Session = Depends(get_db)
):
    """
    Submit supervisor review decision (CONFIRMED anomaly vs DISMISSED false alarm).
    Stores feedback entry and updates flag status in database.
    """
    flag = db.query(AnomalyFlag).filter(AnomalyFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail=f"Anomaly flag '{flag_id}' not found.")

    decision_clean = data.decision.upper()
    if decision_clean not in ("CONFIRMED", "DISMISSED"):
        raise HTTPException(status_code=400, detail="Decision must be 'CONFIRMED' or 'DISMISSED'.")

    # Update flag status
    flag.status = decision_clean

    # Store supervisor feedback
    feedback = SupervisorFeedback(
        flag_id=flag.id,
        supervisor_id=data.supervisor_id,
        decision=decision_clean,
        comments=data.comments
    )

    # Log audit entry
    audit = AuditLog(
        actor_id=data.supervisor_id,
        actor_role="SUPERVISOR",
        action="SUBMIT_SUPERVISOR_FEEDBACK",
        entity_type="anomaly_flags",
        entity_id=flag.id,
        details={
            "decision": decision_clean,
            "comments": data.comments,
            "detector_type": flag.detector_type,
            "severity": flag.severity,
            "score": flag.score
        }
    )

    db.add(feedback)
    db.add(audit)
    db.commit()
    db.refresh(flag)

    return {
        "status": "success",
        "message": f"Supervisor decision '{decision_clean}' stored for flag '{flag.id}'.",
        "flag_status": flag.status,
        "feedback_id": feedback.id
    }

@router.post("/fusion/calibrate")
def calibrate_fusion_weights(
    survey_code: str = "PLFS_2024",
    db: Session = Depends(get_db)
):
    """
    Active Learning Calibration Endpoint:
    Triggers Bayesian weight recalibration of Fusion Engine weights (w_rule, w_stat, w_ml)
    based on supervisor decision history.
    """
    res = FeedbackCalibrationEngine.recalibrate_fusion_weights(db, survey_code)
    return res
