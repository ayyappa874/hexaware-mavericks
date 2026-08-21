from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.models.schema import Survey
from app.engines.temporal_engine import TemporalDriftEngine

router = APIRouter()

@router.get("/dashboard/temporal-drift")
def get_temporal_drift(
    survey_code: str = "PLFS_2024",
    state_code: Optional[str] = None,
    indicator: Optional[str] = None, # lfpr, wpr, ur
    db: Session = Depends(get_db)
):
    """
    Get round-over-round indicator comparison (LFPR, WPR, Unemployment Rate)
    and statistically significant drift flags across MoSPI survey rounds.
    """
    survey = db.query(Survey).filter(Survey.code == survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_code}' not found.")

    res = TemporalDriftEngine.detect_temporal_drift(db, survey.id, state_code=state_code)
    
    # Filter indicator if specific indicator requested
    if indicator and indicator.lower() in ("lfpr", "wpr", "ur") and "drift_analysis" in res:
        ind_key = indicator.lower()
        for item in res["drift_analysis"]:
            item["indicators"] = {ind_key: item["indicators"].get(ind_key)}

    return res
