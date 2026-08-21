import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class RuleViolation(BaseModel):
    rule_id: Optional[str] = None
    rule_code: str
    rule_name: str
    category: str # referential_integrity, existential_integrity, range_check, logical_consistency
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    error_message: str
    evidence: Dict[str, Any]

class ValidationResult(BaseModel):
    is_valid: bool
    anomaly_score: float # 0.0 (perfect) to 1.0 (severe anomaly)
    highest_severity: str # NONE, LOW, MEDIUM, HIGH, CRITICAL
    violations: List[RuleViolation]
    summary_bullets: List[str]

SEVERITY_WEIGHTS = {
    "LOW": 0.25,
    "MEDIUM": 0.50,
    "HIGH": 0.75,
    "CRITICAL": 1.00
}

class RuleEngine:
    """
    Validation Rule Engine for Survey Sentinel.
    Evaluates individual survey record payloads against JSON-defined rules.
    """

    @staticmethod
    def evaluate_rule(rule_json: Dict[str, Any], payload: Dict[str, Any], category: str) -> Optional[Dict[str, Any]]:
        """
        Evaluates a single JSON rule against a payload dict.
        Returns evidence dict if rule fails, or None if rule passes.
        """
        try:
            if category == "existential_integrity":
                target_field = rule_json.get("field")
                if target_field not in payload or payload[target_field] is None or payload[target_field] == "":
                    return {
                        "field": target_field,
                        "value": payload.get(target_field),
                        "reason": f"Field '{target_field}' is missing or null."
                    }

            elif category == "referential_integrity":
                target_field = rule_json.get("field")
                val = payload.get(target_field)
                if val is None:
                    return None # Handled by existential integrity if required
                
                op = rule_json.get("operator")
                allowed_values = rule_json.get("values", [])

                if op == "in_list" and val not in allowed_values:
                    # Check string padding if needed
                    str_val = str(val).zfill(2) if isinstance(val, (int, str)) and len(str(val)) <= 2 else str(val)
                    if str_val not in [str(v) for v in allowed_values]:
                        return {
                            "field": target_field,
                            "value": val,
                            "allowed_values": allowed_values[:10],
                            "reason": f"Value '{val}' for field '{target_field}' is not in valid reference list."
                        }

            elif category == "range_check":
                target_field = rule_json.get("field")
                val = payload.get(target_field)
                if val is None:
                    return None

                op = rule_json.get("operator")
                if op == "between":
                    min_val = rule_json.get("min")
                    max_val = rule_json.get("max")
                    if not (min_val <= val <= max_val):
                        return {
                            "field": target_field,
                            "value": val,
                            "min": min_val,
                            "max": max_val,
                            "reason": f"Field '{target_field}' value {val} is out of valid range [{min_val}, {max_val}]."
                        }
                elif op == "in_set":
                    allowed_set = rule_json.get("set", [])
                    if val not in allowed_set:
                        return {
                            "field": target_field,
                            "value": val,
                            "allowed_set": allowed_set,
                            "reason": f"Field '{target_field}' value {val} not in allowed set {allowed_set}."
                        }

            elif category == "logical_consistency":
                condition = rule_json.get("condition", {})
                assertion = rule_json.get("assertion", {})

                if not condition or not assertion:
                    return None

                # Check if condition triggers
                cond_field = condition.get("field")
                cond_op = condition.get("operator")
                cond_val = condition.get("value")
                cond_in = condition.get("in", [])

                condition_met = False
                actual_cond_val = payload.get(cond_field)

                if cond_op == "equals" and actual_cond_val == cond_val:
                    condition_met = True
                elif cond_op == "in" and actual_cond_val in cond_in:
                    condition_met = True
                elif cond_op == "gte" and actual_cond_val is not None and actual_cond_val >= cond_val:
                    condition_met = True

                # If condition met, evaluate assertion
                if condition_met:
                    assert_field = assertion.get("field")
                    assert_op = assertion.get("operator")
                    assert_val = assertion.get("value")
                    assert_in = assertion.get("in", [])

                    actual_assert_val = payload.get(assert_field)
                    assertion_passed = True

                    if assert_op == "gte":
                        if actual_assert_val is None or actual_assert_val < assert_val:
                            assertion_passed = False
                    elif assert_op == "lte":
                        if actual_assert_val is None or actual_assert_val > assert_val:
                            assertion_passed = False
                    elif assert_op == "equals":
                        if actual_assert_val != assert_val:
                            assertion_passed = False
                    elif assert_op == "in":
                        if actual_assert_val not in assert_in:
                            assertion_passed = False

                    if not assertion_passed:
                        return {
                            "condition_field": cond_field,
                            "condition_value": actual_cond_val,
                            "assertion_field": assert_field,
                            "assertion_actual_value": actual_assert_val,
                            "assertion_expected": f"{assert_op} {assert_val if assert_val is not None else assert_in}",
                            "reason": f"Logical inconsistency: When '{cond_field}' is {actual_cond_val}, '{assert_field}' must be {assert_op} {assert_val if assert_val is not None else assert_in}, but got {actual_assert_val}."
                        }

        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return {"error": str(e)}

        return None

    def validate_record(self, record_payload: Dict[str, Any], rules: List[Any]) -> ValidationResult:
        """
        Validates a single record payload against a list of rule model objects or dicts.
        """
        violations: List[RuleViolation] = []
        summary_bullets: List[str] = []
        max_severity_weight = 0.0
        highest_severity = "NONE"

        for r in rules:
            # Handle SQLAlchemy model or dict
            r_id = getattr(r, "id", r.get("id") if isinstance(r, dict) else None)
            r_code = getattr(r, "rule_code", r.get("rule_code") if isinstance(r, dict) else "")
            r_name = getattr(r, "name", r.get("name") if isinstance(r, dict) else "")
            r_cat = getattr(r, "category", r.get("category") if isinstance(r, dict) else "")
            r_sev = getattr(r, "severity", r.get("severity") if isinstance(r, dict) else "MEDIUM")
            r_json = getattr(r, "rule_json", r.get("rule_json") if isinstance(r, dict) else {})
            r_active = getattr(r, "is_active", r.get("is_active", True) if isinstance(r, dict) else True)

            if not r_active:
                continue

            evidence = self.evaluate_rule(r_json, record_payload, r_cat)
            if evidence:
                err_msg = r_json.get("error_message", evidence.get("reason", "Rule validation failed."))
                
                violation = RuleViolation(
                    rule_id=r_id,
                    rule_code=r_code,
                    rule_name=r_name,
                    category=r_cat,
                    severity=r_sev,
                    error_message=err_msg,
                    evidence=evidence
                )
                violations.append(violation)

                bullet = f"[{r_sev}] {r_name}: {err_msg} ({evidence.get('reason', '')})"
                summary_bullets.append(bullet)

                sev_weight = SEVERITY_WEIGHTS.get(r_sev, 0.5)
                if sev_weight > max_severity_weight:
                    max_severity_weight = sev_weight
                    highest_severity = r_sev

        # Anomaly score calculation
        anomaly_score = 0.0
        if violations:
            # Aggregate severity score normalized between 0.0 and 1.0
            total_sev = sum(SEVERITY_WEIGHTS.get(v.severity, 0.5) for v in violations)
            anomaly_score = round(min(1.0, total_sev / 2.5), 3)

        is_valid = len(violations) == 0

        return ValidationResult(
            is_valid=is_valid,
            anomaly_score=anomaly_score,
            highest_severity=highest_severity,
            violations=violations,
            summary_bullets=summary_bullets
        )
