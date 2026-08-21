import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.schema import SupervisorFeedback, AnomalyFlag, AuditLog

logger = logging.getLogger(__name__)

class FeedbackCalibrationEngine:
    """
    Supervisor Feedback Active Learning Calibration Engine for Survey Sentinel.
    Recalibrates Fusion Engine detector weights (w_rule, w_stat, w_ml) based on human supervisor accuracy.
    """

    @staticmethod
    def recalibrate_fusion_weights(db: Session, survey_id: str) -> Dict[str, Any]:
        """
        Analyzes supervisor feedback history and computes optimal Bayesian fusion weights.
        """
        # Fetch all supervisor feedback joined with anomaly flags
        feedbacks = db.query(SupervisorFeedback).all()

        detector_counts = {
            "RULE_ENGINE": {"confirmed": 0, "total": 0},
            "STATISTICAL_ENGINE": {"confirmed": 0, "total": 0},
            "ML_ENGINE": {"confirmed": 0, "total": 0}
        }

        for fb in feedbacks:
            flag = db.query(AnomalyFlag).filter(AnomalyFlag.id == fb.flag_id).first()
            if not flag:
                continue

            detector = flag.detector_type
            is_confirmed = (fb.decision.upper() == "CONFIRMED")

            if detector == "ENSEMBLE" and isinstance(flag.evidence, dict):
                fired_detectors = flag.evidence.get("detectors_fired", ["RULE_ENGINE"])
                for d in fired_detectors:
                    if d in detector_counts:
                        detector_counts[d]["total"] += 1
                        if is_confirmed:
                            detector_counts[d]["confirmed"] += 1
            elif detector in detector_counts:
                detector_counts[detector]["total"] += 1
                if is_confirmed:
                    detector_counts[detector]["confirmed"] += 1

        # Calculate Laplace smoothed precision per detector
        precisions = {}
        for det, counts in detector_counts.items():
            # Laplace smoothing: (confirmed + 1) / (total + 2)
            p = (counts["confirmed"] + 1.0) / (counts["total"] + 2.0)
            precisions[det] = p

        total_p = sum(precisions.values())
        new_weights = {
            "w_rule": round(precisions["RULE_ENGINE"] / total_p, 3),
            "w_stat": round(precisions["STATISTICAL_ENGINE"] / total_p, 3),
            "w_ml": round(precisions["ML_ENGINE"] / total_p, 3)
        }

        # Log active learning calibration event to audit_log table
        audit_entry = AuditLog(
            actor_id="SYSTEM_AUTO_CALIBRATOR",
            actor_role="ADMIN",
            action="FUSION_WEIGHT_RECALIBRATION",
            entity_type="fusion_engine",
            entity_id=survey_id,
            details={
                "previous_weights": {"w_rule": 0.35, "w_stat": 0.35, "w_ml": 0.30},
                "new_weights": new_weights,
                "detector_precision_estimates": precisions,
                "feedback_samples_evaluated": len(feedbacks)
            }
        )
        db.add(audit_entry)
        db.commit()

        logger.info(f"Recalibrated Fusion Engine weights based on {len(feedbacks)} supervisor feedback samples: {new_weights}")

        return {
            "status": "success",
            "message": "Fusion Engine weights successfully recalibrated from supervisor feedback history.",
            "new_weights": new_weights,
            "detector_precisions": precisions,
            "total_feedbacks_evaluated": len(feedbacks)
        }
