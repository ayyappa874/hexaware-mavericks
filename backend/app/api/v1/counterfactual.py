from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schema import Survey
from app.engines.counterfactual_engine import CounterfactualEngine

router = APIRouter()

@router.get("/records/{record_id}/counterfactual")
def get_record_counterfactual(
    record_id: str,
    survey_code: str = "PLFS_2024",
    db: Session = Depends(get_db)
):
    """
    Get prescriptive counterfactual recommendations ("What needs to change for this record to be normal?")
    for a specific PLFS record.
    """
    survey = db.query(Survey).filter(Survey.code == survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_code}' not found.")

    res = CounterfactualEngine.generate_counterfactuals(db, survey.id, record_id)
    if res["status"] == "error":
        raise HTTPException(status_code=404, detail=res["message"])

    return res
