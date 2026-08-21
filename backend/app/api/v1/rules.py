from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.schema import Survey, ValidationRule, AuditLog
from app.core.security import require_role

router = APIRouter()

class RuleCreateInput(BaseModel):
    survey_code: str = "PLFS_2024"
    rule_code: str
    name: str
    category: str # referential_integrity, existential_integrity, range_check, logical_consistency
    severity: str = "MEDIUM" # LOW, MEDIUM, HIGH, CRITICAL
    rule_json: Dict[str, Any]
    is_active: bool = True

class RuleUpdateInput(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    rule_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

@router.get("/rules")
def list_rules(survey_code: Optional[str] = None, db: Session = Depends(get_db)):
    """
    List all validation rules stored in the database for a survey.
    """
    query = db.query(ValidationRule)
    if survey_code:
        survey = db.query(Survey).filter(Survey.code == survey_code).first()
        if survey:
            query = query.filter(ValidationRule.survey_id == survey.id)

    rules = query.order_by(ValidationRule.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "survey_id": r.survey_id,
            "rule_code": r.rule_code,
            "name": r.name,
            "category": r.category,
            "severity": r.severity,
            "rule_json": r.rule_json,
            "is_active": r.is_active,
            "created_at": r.created_at
        }
        for r in rules
    ]

@router.post("/rules")
def create_rule(
    data: RuleCreateInput,
    db: Session = Depends(get_db),
    user_info: dict = Depends(require_role(["Admin"]))
):
    """
    Create a new configurable JSON validation rule in the database.
    """
    survey = db.query(Survey).filter(Survey.code == data.survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{data.survey_code}' not found.")

    existing = db.query(ValidationRule).filter(
        ValidationRule.survey_id == survey.id,
        ValidationRule.rule_code == data.rule_code
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"Rule code '{data.rule_code}' already exists for survey.")

    rule = ValidationRule(
        survey_id=survey.id,
        rule_code=data.rule_code,
        name=data.name,
        category=data.category,
        severity=data.severity,
        rule_json=data.rule_json,
        is_active=data.is_active
    )

    db.add(rule)

    audit = AuditLog(
        entity_type="validation_rules",
        entity_id=rule.id,
        action="RULE_CREATE",
        actor_id=user_info.get("username", "admin"),
        actor_role=user_info.get("role", "Admin"),
        details={"rule_code": rule.rule_code, "category": rule.category, "severity": rule.severity}
    )
    db.add(audit)

    db.commit()
    db.refresh(rule)

    return {
        "status": "success",
        "message": f"Rule '{rule.rule_code}' created successfully",
        "rule": {
            "id": rule.id,
            "rule_code": rule.rule_code,
            "name": rule.name,
            "category": rule.category,
            "severity": rule.severity,
            "is_active": rule.is_active
        }
    }

@router.put("/rules/{rule_id}")
def update_rule(rule_id: str, data: RuleUpdateInput, db: Session = Depends(get_db)):
    """
    Update an existing JSON validation rule without changing application code.
    """
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        # Also try lookup by rule_code
        rule = db.query(ValidationRule).filter(ValidationRule.rule_code == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")

    if data.name is not None: rule.name = data.name
    if data.category is not None: rule.category = data.category
    if data.severity is not None: rule.severity = data.severity
    if data.rule_json is not None: rule.rule_json = data.rule_json
    if data.is_active is not None: rule.is_active = data.is_active

    db.commit()
    db.refresh(rule)

    return {
        "status": "success",
        "message": f"Rule '{rule.rule_code}' updated successfully",
        "rule": {
            "id": rule.id,
            "rule_code": rule.rule_code,
            "name": rule.name,
            "category": rule.category,
            "severity": rule.severity,
            "rule_json": rule.rule_json,
            "is_active": rule.is_active
        }
    }

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    """
    Delete a validation rule.
    """
    rule = db.query(ValidationRule).filter(ValidationRule.id == rule_id).first()
    if not rule:
        rule = db.query(ValidationRule).filter(ValidationRule.rule_code == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")

    db.delete(rule)
    db.commit()
    return {"status": "success", "message": f"Rule '{rule_id}' deleted successfully."}
