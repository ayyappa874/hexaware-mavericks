import pytest
import sys
import os

# Ensure app imports work cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.engines.rule_engine import RuleEngine, ValidationResult

@pytest.fixture
def sample_rules():
    return [
        {
            "rule_code": "RULE_STATE_RANGE",
            "name": "State Code Referential Integrity",
            "category": "referential_integrity",
            "severity": "HIGH",
            "is_active": True,
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
            "is_active": True,
            "rule_json": {
                "field": "Age",
                "operator": "not_null",
                "error_message": "Age field is mandatory."
            }
        },
        {
            "rule_code": "RULE_AGE_RANGE",
            "name": "Age Valid Demographic Range",
            "category": "range_check",
            "severity": "HIGH",
            "is_active": True,
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
            "is_active": True,
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
                "error_message": "Person under 15 years cannot be Regular Salaried."
            }
        },
        {
            "rule_code": "RULE_HEAD_RELATION",
            "name": "Person 1 Relationship to Head Consistency",
            "category": "logical_consistency",
            "severity": "HIGH",
            "is_active": True,
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
                "error_message": "Person 1 must be Head of Household."
            }
        },
        {
            "rule_code": "RULE_INACTIVE_ZERO_WAGES",
            "name": "Inactive Persons Zero Wage Check",
            "category": "logical_consistency",
            "severity": "HIGH",
            "is_active": True,
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
                "error_message": "Inactive persons must have zero daily wage."
            }
        }
    ]

def test_valid_plfs_record_passes_all_rules(sample_rules):
    engine = RuleEngine()
    valid_record = {
        "Survey_Round": "2024-25",
        "State": "09",
        "District": "001",
        "Sector": "1",
        "Person_No": 1,
        "Rel_To_Head": 1,
        "Sex": 1,
        "Age": 35,
        "General_Edu": 10,
        "Usual_Principal_Activity_Status": 31, # Regular Salaried
        "Daily_Wages": 850.0,
        "Earnings_Last_Month": 25000.0,
        "Monthly_Exp": 18000.0
    }

    result = engine.validate_record(valid_record, sample_rules)
    assert result.is_valid is True
    assert len(result.violations) == 0
    assert result.anomaly_score == 0.0

def test_referential_integrity_violation(sample_rules):
    engine = RuleEngine()
    invalid_state_record = {
        "State": "99", # Invalid state code
        "Age": 30,
        "Person_No": 1,
        "Rel_To_Head": 1,
        "Usual_Principal_Activity_Status": 11,
        "Daily_Wages": 0.0
    }

    result = engine.validate_record(invalid_state_record, sample_rules)
    assert result.is_valid is False
    codes = [v.rule_code for v in result.violations]
    assert "RULE_STATE_RANGE" in codes

def test_existential_integrity_violation(sample_rules):
    engine = RuleEngine()
    missing_age_record = {
        "State": "09",
        "Age": None, # Missing Age
        "Person_No": 1,
        "Rel_To_Head": 1
    }

    result = engine.validate_record(missing_age_record, sample_rules)
    assert result.is_valid is False
    codes = [v.rule_code for v in result.violations]
    assert "RULE_EXISTENTIAL_AGE" in codes

def test_range_check_violation(sample_rules):
    engine = RuleEngine()
    out_of_bounds_age_record = {
        "State": "09",
        "Age": 140, # Age > 110
        "Person_No": 1,
        "Rel_To_Head": 1
    }

    result = engine.validate_record(out_of_bounds_age_record, sample_rules)
    assert result.is_valid is False
    codes = [v.rule_code for v in result.violations]
    assert "RULE_AGE_RANGE" in codes

def test_logical_consistency_child_salaried_worker(sample_rules):
    engine = RuleEngine()
    child_salaried_record = {
        "State": "27",
        "Age": 10, # Age < 15
        "Usual_Principal_Activity_Status": 31, # Regular Salaried
        "Person_No": 2,
        "Rel_To_Head": 3,
        "Daily_Wages": 500.0
    }

    result = engine.validate_record(child_salaried_record, sample_rules)
    assert result.is_valid is False
    codes = [v.rule_code for v in result.violations]
    assert "RULE_MIN_AGE_SALARIED" in codes

def test_logical_consistency_person1_not_head(sample_rules):
    engine = RuleEngine()
    bad_head_record = {
        "State": "19",
        "Age": 40,
        "Person_No": 1,
        "Rel_To_Head": 3 # Should be 1 (Self/Head)
    }

    result = engine.validate_record(bad_head_record, sample_rules)
    assert result.is_valid is False
    codes = [v.rule_code for v in result.violations]
    assert "RULE_HEAD_RELATION" in codes

def test_logical_consistency_student_with_wages(sample_rules):
    engine = RuleEngine()
    student_with_wages = {
        "State": "33",
        "Age": 19,
        "Person_No": 2,
        "Rel_To_Head": 3,
        "Usual_Principal_Activity_Status": 81, # Student / Inactive
        "Daily_Wages": 450.0 # Should be 0.0
    }

    result = engine.validate_record(student_with_wages, sample_rules)
    assert result.is_valid is False
    codes = [v.rule_code for v in result.violations]
    assert "RULE_INACTIVE_ZERO_WAGES" in codes
