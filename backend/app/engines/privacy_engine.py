import random
import math
from typing import Dict, Any

class DifferentialPrivacyEngine:
    """
    Differential Privacy Export Layer.
    Applies calibrated Laplace noise to aggregate statistics before external export.
    Noise scale b = Sensitivity / Epsilon.
    """

    @staticmethod
    def sample_laplace(b: float) -> float:
        u = random.random() - 0.5
        return -b * math.copysign(1.0, u) * math.log(1.0 - 2.0 * abs(u))

    @staticmethod
    def sanitize_aggregates(stats: Dict[str, Any], privacy_budget: str = "medium") -> Dict[str, Any]:
        # Epsilon privacy budgets
        epsilons = {
            "low": 0.5,       # High privacy, more noise
            "medium": 1.0,    # Balanced privacy
            "high": 2.0       # Low noise, exact accuracy
        }

        eps = epsilons.get(privacy_budget.lower(), 1.0)
        sensitivity = 1.0
        b = sensitivity / eps

        sanitized = stats.copy()
        for k in ["total_records", "high_priority_count", "mean_risk_score"]:
            if k in sanitized and isinstance(sanitized[k], (int, float)):
                noise = DifferentialPrivacyEngine.sample_laplace(b)
                if isinstance(sanitized[k], int):
                    sanitized[k] = max(int(round(sanitized[k] + noise)), 0)
                else:
                    sanitized[k] = max(round(sanitized[k] + noise, 1), 0.0)

        sanitized["_privacy_meta"] = {
            "differential_privacy_applied": True,
            "privacy_budget": privacy_budget,
            "epsilon": eps,
            "laplace_scale_b": round(b, 3)
        }
        return sanitized
