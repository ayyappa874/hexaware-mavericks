import logging
from typing import Dict, Any, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class FusionResult(BaseModel):
    overall_risk: int # 0 to 100
    risk_band: str # NORMAL, MONITOR, REVIEW, HIGH_PRIORITY
    rule_score: float # 0.0 to 1.0
    stat_score: float # 0.0 to 1.0
    ml_score: float # 0.0 to 1.0
    weights_used: Dict[str, float]
    agreement_count: int # Number of independent engines that flagged (0 to 3)

class FusionEngine:
    """
    Weighted Ensemble Fusion Engine for Survey Sentinel.
    Combines Rule, Statistical, and ML detector signals into an overall risk score (0-100)
    and risk classification band.
    """

    def __init__(self, w_rule: float = 0.35, w_stat: float = 0.35, w_ml: float = 0.30):
        self.w_rule = w_rule
        self.w_stat = w_stat
        self.w_ml = w_ml

    def fuse(self, rule_score: float, stat_score: float, ml_score: float) -> FusionResult:
        """
        Combines detector scores into an overall risk score (0-100) and risk band.
        """
        # Ensure scores normalized between 0.0 and 1.0
        r_score = min(1.0, max(0.0, rule_score))
        s_score = min(1.0, max(0.0, stat_score))
        m_score = min(1.0, max(0.0, ml_score))

        # Weighted combination
        raw_weighted = (self.w_rule * r_score) + (self.w_stat * s_score) + (self.w_ml * m_score)
        
        # Agreement boost if multiple independent engines flag simultaneously
        agreement_count = sum([1 for score in [r_score, s_score, m_score] if score >= 0.40])
        boost = 1.15 if agreement_count >= 2 else 1.0

        overall_risk = int(round(min(100.0, raw_weighted * 100.0 * boost)))

        # Risk Classification Bands
        if overall_risk <= 25:
            risk_band = "NORMAL"
        elif 26 <= overall_risk <= 50:
            risk_band = "MONITOR"
        elif 51 <= overall_risk <= 75:
            risk_band = "REVIEW"
        else:
            risk_band = "HIGH_PRIORITY"

        return FusionResult(
            overall_risk=overall_risk,
            risk_band=risk_band,
            rule_score=round(r_score, 3),
            stat_score=round(s_score, 3),
            ml_score=round(m_score, 3),
            weights_used={"rule": self.w_rule, "stat": self.w_stat, "ml": self.w_ml},
            agreement_count=agreement_count
        )
