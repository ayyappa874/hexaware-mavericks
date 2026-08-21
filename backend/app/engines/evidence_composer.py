import logging
from typing import Dict, Any, List
from app.engines.rule_engine import ValidationResult
from app.engines.statistical_engine import StatisticalResult
from app.engines.ml_engine import MLResult
from app.engines.fusion_engine import FusionResult

logger = logging.getLogger(__name__)

def to_dict(obj: Any) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    return dict(obj)

class EvidenceComposer:
    """
    Evidence Composer for Survey Sentinel.
    Synthesizes multi-detector outputs into structured JSON evidence and 3-5 dynamic, non-templated
    human-readable narrative bullets.
    """

    @staticmethod
    def compose_evidence(
        payload: Dict[str, Any],
        rule_res: ValidationResult,
        stat_res: StatisticalResult,
        ml_res: MLResult,
        fusion_res: FusionResult
    ) -> Dict[str, Any]:

        detectors_fired = []
        if not rule_res.is_valid:
            detectors_fired.append("RULE_ENGINE")
        if stat_res.outliers:
            detectors_fired.append("STATISTICAL_ENGINE")
        if ml_res.is_anomaly:
            detectors_fired.append("ML_ENGINE")

        narrative_bullets: List[str] = []

        # 1. Headline summary bullet based on risk band and detector agreement
        state = payload.get("State", "00")
        fsu = payload.get("FSU", "FSU")
        
        if fusion_res.agreement_count >= 2:
            headline = f"High-confidence anomaly flagged by {fusion_res.agreement_count} independent detection layers in State {state} (FSU {fsu}). Overall risk score: {fusion_res.overall_risk}/100 [{fusion_res.risk_band}]."
        elif detectors_fired:
            headline = f"Pattern requires supervisory review in State {state} (FSU {fsu}) with overall risk score {fusion_res.overall_risk}/100 [{fusion_res.risk_band}]."
        else:
            headline = f"Record evaluated within normal parameters for State {state} peer cohort (Risk Score: {fusion_res.overall_risk}/100)."

        narrative_bullets.append(headline)

        # 2. Rule violation bullets
        for v in rule_res.violations:
            rule_msg = f"Rule Violation ({v.severity}): {v.rule_name} — {v.error_message}"
            narrative_bullets.append(rule_msg)

        # 3. Statistical peer cohort bullets
        for out in stat_res.outliers:
            stat_msg = f"Cohort Deviation: {out.deviation_description}"
            narrative_bullets.append(stat_msg)

        # 4. ML multivariate anomaly bullet
        if ml_res.is_anomaly:
            ml_msg = f"Multivariate Outlier: Isolation Forest score {ml_res.combined_ml_score:.2f} driven by unusual joint distribution across {', '.join(ml_res.top_contributing_features)}."
            narrative_bullets.append(ml_msg)

        # 5. Cohort context or detector summary bullet
        if stat_res.cohort_size > 0:
            cohort_bullet = f"Peer Cohort Context: Evaluated against baseline of {stat_res.cohort_size} sample records sharing same State ({state}), Sector ({payload.get('Sector', '1')}), and Activity Status ({payload.get('Usual_Principal_Activity_Status', 'N/A')})."
            narrative_bullets.append(cohort_bullet)
        else:
            sparse_bullet = f"Peer Cohort Context: Record assigned to peer cohort '{stat_res.cohort_key}' for regional demographic validation."
            narrative_bullets.append(sparse_bullet)

        # 6. Recommendation bullet to ensure 3 to 5 bullets minimum
        if len(narrative_bullets) < 3:
            rec_bullet = f"Supervisory Action: Standard verification recommended per MoSPI CAPI protocol for risk band '{fusion_res.risk_band}'."
            narrative_bullets.append(rec_bullet)

        # Clamp bullets to range [3, 5]
        narrative_bullets = narrative_bullets[:5]

        evidence_payload = {
            "overall_risk": fusion_res.overall_risk,
            "risk_band": fusion_res.risk_band,
            "detectors_fired": detectors_fired,
            "detector_agreement_count": fusion_res.agreement_count,
            "fusion": to_dict(fusion_res),
            "rule_evidence": {
                "is_valid": rule_res.is_valid,
                "highest_severity": rule_res.highest_severity,
                "violations": [to_dict(v) for v in rule_res.violations]
            },
            "statistical_evidence": {
                "cohort_key": stat_res.cohort_key,
                "cohort_size": stat_res.cohort_size,
                "anomaly_score": stat_res.anomaly_score,
                "highest_z_score": stat_res.highest_z_score,
                "outliers": [to_dict(o) for o in stat_res.outliers]
            },
            "ml_evidence": {
                "combined_ml_score": ml_res.combined_ml_score,
                "iforest_score": ml_res.iforest_score,
                "lof_score": ml_res.lof_score,
                "is_anomaly": ml_res.is_anomaly,
                "top_contributing_features": ml_res.top_contributing_features
            },
            "narrative_bullets": narrative_bullets
        }

        return evidence_payload
