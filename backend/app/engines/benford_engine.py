import math
from typing import List, Dict, Any, Tuple

BENFORD_EXPECTED = {
    1: 0.301,
    2: 0.176,
    3: 0.125,
    4: 0.097,
    5: 0.079,
    6: 0.067,
    7: 0.058,
    8: 0.051,
    9: 0.046
}

class BenfordEngine:
    """
    Forensic Benford's Law Module for leading-digit distribution analysis.
    Performs Chi-Square Goodness-of-Fit test with Benjamini-Hochberg FDR correction.
    """

    @staticmethod
    def get_leading_digit(val: float) -> int:
        try:
            val_str = str(abs(val)).lstrip("0").replace(".", "")
            if val_str and val_str[0].isdigit() and val_str[0] != "0":
                return int(val_str[0])
        except Exception:
            pass
        return 0

    @staticmethod
    def analyze_digits(values: List[float]) -> Dict[str, Any]:
        valid_digits = [BenfordEngine.get_leading_digit(v) for v in values]
        digits_only = [d for d in valid_digits if d in BENFORD_EXPECTED]
        total = len(digits_only)

        if total < 10:
            return {
                "total_samples": total,
                "is_conforming": True,
                "chi_square_stat": 0.0,
                "p_value": 1.0,
                "digit_counts": {d: 0 for d in range(1, 10)},
                "observed_distribution": {d: BENFORD_EXPECTED[d] for d in range(1, 10)},
                "expected_distribution": BENFORD_EXPECTED
            }

        counts = {d: 0 for d in range(1, 10)}
        for d in digits_only:
            counts[d] += 1

        chi_sq = 0.0
        observed_dist = {}
        for d in range(1, 10):
            obs_prob = counts[d] / total
            exp_prob = BENFORD_EXPECTED[d]
            exp_count = exp_prob * total
            chi_sq += ((counts[d] - exp_count) ** 2) / exp_count
            observed_dist[d] = round(obs_prob, 4)

        # Critical value for 8 degrees of freedom at alpha=0.05 is 15.507
        is_conforming = bool(chi_sq < 15.507)
        anomaly_score = min(max((chi_sq - 15.507) / 30.0, 0.0), 1.0) if not is_conforming else 0.0

        return {
            "total_samples": total,
            "is_conforming": is_conforming,
            "chi_square_stat": round(chi_sq, 2),
            "anomaly_score": round(anomaly_score, 3),
            "digit_counts": counts,
            "observed_distribution": observed_dist,
            "expected_distribution": BENFORD_EXPECTED
        }

    @staticmethod
    def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
        """
        Benjamini-Hochberg False Discovery Rate (FDR) procedure.
        """
        n = len(p_values)
        if n == 0:
            return []

        sorted_indices = sorted(range(n), key=lambda i: p_values[i])
        sorted_p = [p_values[i] for i in sorted_indices]

        significant = [False] * n
        max_k = -1

        for k in range(n - 1, -1, -1):
            if sorted_p[k] <= ((k + 1) / n) * alpha:
                max_k = k
                break

        if max_k >= 0:
            for k in range(max_k + 1):
                significant[sorted_indices[k]] = True

        return significant
