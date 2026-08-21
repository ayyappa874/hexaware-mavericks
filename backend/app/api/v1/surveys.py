from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.session import get_db
from app.models.schema import Survey, ValidationRule

router = APIRouter()

@router.get("/surveys")
def list_surveys(db: Session = Depends(get_db)):
    """
    List all registered survey schemas in Survey Sentinel.
    """
    surveys = db.query(Survey).filter(Survey.is_active == True).all()
    return [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "description": s.description,
            "column_count": len(s.schema_definition.get("columns", [])),
            "created_at": s.created_at,
            "updated_at": s.updated_at
        }
        for s in surveys
    ]

@router.get("/surveys/{survey_id}")
def get_survey_schema(survey_id: str, db: Session = Depends(get_db)):
    """
    Retrieve full schema definition and validation rules for a registered survey.
    """
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        # Also try lookup by code
        survey = db.query(Survey).filter(Survey.code == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_id}' not found in registry.")

    rules = db.query(ValidationRule).filter(ValidationRule.survey_id == survey.id).all()

    return {
        "id": survey.id,
        "code": survey.code,
        "name": survey.name,
        "description": survey.description,
        "schema_definition": survey.schema_definition,
        "rules": [
            {
                "id": r.id,
                "rule_code": r.rule_code,
                "name": r.name,
                "category": r.category,
                "severity": r.severity,
                "rule_json": r.rule_json,
                "is_active": r.is_active
            }
            for r in rules
        ],
        "created_at": survey.created_at
    }
