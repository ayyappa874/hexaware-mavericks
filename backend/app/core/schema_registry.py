import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.schema import Survey, ValidationRule
from app.core.data_loader import PLFSDataLoader

logger = logging.getLogger(__name__)

def register_plfs_survey(db: Session, layout_path: str = "data/plfs_layout.json") -> Survey:
    """
    Registers or updates the official PLFS survey schema in the Postgres 'surveys' registry table.
    """
    loader = PLFSDataLoader(layout_path)
    schema_map = loader.schema_map

    survey_code = schema_map["survey_code"]
    survey = db.query(Survey).filter(Survey.code == survey_code).first()

    if not survey:
        survey = Survey(
            code=survey_code,
            name=schema_map["survey_name"],
            description=schema_map["description"],
            schema_definition=schema_map,
            is_active=True
        )
        db.add(survey)
        db.commit()
        db.refresh(survey)
        logger.info(f"Registered new survey '{survey.name}' (Code: {survey.code}, ID: {survey.id}) in schema registry.")
    else:
        survey.name = schema_map["survey_name"]
        survey.description = schema_map["description"]
        survey.schema_definition = schema_map
        db.commit()
        db.refresh(survey)
        logger.info(f"Updated existing survey '{survey.name}' schema in registry.")

    # Register default configurable validation rules for Phase 1 Rule Engine
    register_default_validation_rules(db, survey.id)

    return survey

def register_default_validation_rules(db: Session, survey_id: str):
    """
    Registers Phase 1 JSON-defined validation rules for PLFS.
    Stores 10 real PLFS validation rules in validation_rules table.
    """
    default_rules = [
        {
            "rule_code": "RULE_STATE_RANGE",
            "name": "State Code Referential Integrity",
            "category": "referential_integrity",
            "severity": "HIGH",
            "rule_json": {
                "field": "State",
                "operator": "in_list",
                "values": [f"{i:02d}" for i in range(1, 38)],
                "error_message": "State code is invalid or outside standard 01-37 territory list."
            }
        },
        {
            "rule_code": "RULE_EXISTENTIAL_AGE",
            "name": "Age Field Existential Integrity",
            "category": "existential_integrity",
            "severity": "CRITICAL",
            "rule_json": {
                "field": "Age",
                "operator": "not_null",
                "error_message": "Age field is mandatory and must not be null or missing."
            }
        },
        {
            "rule_code": "RULE_AGE_RANGE",
            "name": "Age Valid Demographic Range",
            "category": "range_check",
            "severity": "HIGH",
            "rule_json": {
                "field": "Age",
                "operator": "between",
                "min": 0,
                "max": 110,
                "error_message": "Age must be between 0 and 110 years."
            }
        },
        {
            "rule_code": "RULE_MIN_AGE_SALARIED",
            "name": "Minimum Age for Regular Salaried Employment",
            "category": "logical_consistency",
            "severity": "CRITICAL",
            "rule_json": {
                "condition": {
                    "field": "Usual_Principal_Activity_Status",
                    "operator": "equals",
                    "value": 31
                },
                "assertion": {
                    "field": "Age",
                    "operator": "gte",
                    "value": 15
                },
                "error_message": "Person under 15 years cannot be recorded as Regular Salaried Employee (Activity Status 31)."
            }
        },
        {
            "rule_code": "RULE_MIN_AGE_GRADUATE",
            "name": "Minimum Age for Graduate Degree",
            "category": "logical_consistency",
            "severity": "HIGH",
            "rule_json": {
                "condition": {
                    "field": "General_Edu",
                    "operator": "gte",
                    "value": 12
                },
                "assertion": {
                    "field": "Age",
                    "operator": "gte",
                    "value": 18
                },
                "error_message": "General Educational qualification 'Graduate or above' requires age >= 18."
            }
        },
        {
            "rule_code": "RULE_HEAD_RELATION",
            "name": "Person 1 Relationship to Head Consistency",
            "category": "logical_consistency",
            "severity": "HIGH",
            "rule_json": {
                "condition": {
                    "field": "Person_No",
                    "operator": "equals",
                    "value": 1
                },
                "assertion": {
                    "field": "Rel_To_Head",
                    "operator": "equals",
                    "value": 1
                },
                "error_message": "Person serial number 1 within household must be Head of Household (Rel_To_Head = 1)."
            }
        },
        {
            "rule_code": "RULE_ACTIVITY_CODE_VALID",
            "name": "Usual Principal Activity Status Validity",
            "category": "referential_integrity",
            "severity": "CRITICAL",
            "rule_json": {
                "field": "Usual_Principal_Activity_Status",
                "operator": "in_list",
                "values": [11, 12, 21, 31, 41, 51, 81, 91, 92, 93, 97],
                "error_message": "Usual Principal Activity Status Code is not a valid MoSPI PLFS activity code."
            }
        },
        {
            "rule_code": "RULE_EARNINGS_RANGE",
            "name": "Monthly Earnings Range Bounds",
            "category": "range_check",
            "severity": "MEDIUM",
            "rule_json": {
                "field": "Earnings_Last_Month",
                "operator": "between",
                "min": 0.0,
                "max": 1000000.0,
                "error_message": "Monthly earnings out of realistic range [0, 1,000,000 INR]."
            }
        },
        {
            "rule_code": "RULE_INACTIVE_ZERO_WAGES",
            "name": "Economically Inactive Persons Zero Daily Wage Check",
            "category": "logical_consistency",
            "severity": "HIGH",
            "rule_json": {
                "condition": {
                    "field": "Usual_Principal_Activity_Status",
                    "operator": "in",
                    "in": [81, 91, 92, 93, 97]
                },
                "assertion": {
                    "field": "Daily_Wages",
                    "operator": "equals",
                    "value": 0.0
                },
                "error_message": "Economically inactive status (Student, Domestic, Pensioner) must have Daily Wages equal to 0."
            }
        },
        {
            "rule_code": "RULE_SEX_RANGE",
            "name": "Gender Field Valid Set",
            "category": "range_check",
            "severity": "HIGH",
            "rule_json": {
                "field": "Sex",
                "operator": "in_set",
                "set": [1, 2, 3],
                "error_message": "Sex code must be 1 (Male), 2 (Female), or 3 (Transgender)."
            }
        }
    ]

    for rule_data in default_rules:
        existing = db.query(ValidationRule).filter(
            ValidationRule.survey_id == survey_id,
            ValidationRule.rule_code == rule_data["rule_code"]
        ).first()

        if not existing:
            v_rule = ValidationRule(
                survey_id=survey_id,
                rule_code=rule_data["rule_code"],
                name=rule_data["name"],
                category=rule_data["category"],
                severity=rule_data["severity"],
                rule_json=rule_data["rule_json"],
                is_active=True
            )
            db.add(v_rule)
        else:
            existing.name = rule_data["name"]
            existing.category = rule_data["category"]
            existing.severity = rule_data["severity"]
            existing.rule_json = rule_data["rule_json"]

    db.commit()
    logger.info(f"Registered/updated {len(default_rules)} default PLFS validation rules.")
