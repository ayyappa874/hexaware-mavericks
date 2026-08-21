import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def get_age_bracket(age: Optional[int]) -> str:
    if age is None:
        return "UNKNOWN"
    if age < 18:
        return "UNDER_18"
    elif 18 <= age <= 25:
        return "18_25"
    elif 26 <= age <= 40:
        return "26_40"
    elif 41 <= age <= 60:
        return "41_60"
    else:
        return "OVER_60"

def get_cohort_key(payload: Dict[str, Any]) -> str:
    state = str(payload.get("State", "00")).zfill(2)
    sector = str(payload.get("Sector", "1"))
    age_bracket = get_age_bracket(payload.get("Age"))
    activity = str(payload.get("Usual_Principal_Activity_Status", "0"))
    return f"State:{state}|Sector:{sector}|Age:{age_bracket}|Activity:{activity}"

class StatisticalOutlier(BaseModel):
    field: str
    value: float
    cohort_key: str
    cohort_size: int
    cohort_mean: float
    cohort_median: float
    cohort_std: float
    cohort_iqr_low: float
    cohort_iqr_high: float
    z_score: float
    mad_score: float
    percentile: float
    is_iqr_outlier: bool
    deviation_description: str

class StatisticalResult(BaseModel):
    cohort_key: str
    cohort_size: int
    anomaly_score: float # 0.0 to 1.0
    highest_z_score: float
    outliers: List[StatisticalOutlier]
    evidence_bullets: List[str]

class StatisticalEngine:
    """
    Contextual Statistical Outlier Detector for Survey Sentinel.
    Computes Z-Score, IQR, and MAD strictly PER PEER COHORT.
    """

    def __init__(self):
        self.cohort_stats: Dict[str, Dict[str, Any]] = {}

    def fit(self, records: List[Dict[str, Any]]):
        """
        Fits peer cohort statistical distributions (mean, std, median, IQR, MAD) from baseline records.
        """
        if not records:
            return

        df = pd.DataFrame(records)
        numeric_cols = ["Earnings_Last_Month", "Daily_Wages", "Monthly_Exp"]

        # Ensure numeric types
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            else:
                df[col] = 0.0

        # Construct cohort keys
        df["cohort_key"] = df.apply(get_cohort_key, axis=1)

        grouped = df.groupby("cohort_key")

        self.cohort_stats = {}
        for cohort_key, group in grouped:
            c_size = len(group)
            stats_dict = {"size": c_size, "metrics": {}}

            for col in numeric_cols:
                vals = group[col].values
                mean_val = float(np.mean(vals))
                std_val = float(np.std(vals))
                if std_val < 1e-5:
                    std_val = 1.0 # Avoid division by zero

                q25, median_val, q75 = np.percentile(vals, [25, 50, 75])
                iqr = q75 - q25
                iqr_low = q25 - 1.5 * iqr
                iqr_high = q75 + 1.5 * iqr

                mad = float(np.median(np.abs(vals - median_val)))
                if mad < 1e-5:
                    mad = 1.0

                stats_dict["metrics"][col] = {
                    "mean": round(mean_val, 2),
                    "std": round(std_val, 2),
                    "median": round(float(median_val), 2),
                    "q25": round(float(q25), 2),
                    "q75": round(float(q75), 2),
                    "iqr": round(float(iqr), 2),
                    "iqr_low": round(float(iqr_low), 2),
                    "iqr_high": round(float(iqr_high), 2),
                    "mad": round(mad, 2),
                    "raw_vals": sorted(vals.tolist())
                }

            self.cohort_stats[cohort_key] = stats_dict

        logger.info(f"Fitted StatisticalEngine across {len(self.cohort_stats)} peer cohorts.")

    def evaluate_record(self, payload: Dict[str, Any]) -> StatisticalResult:
        """
        Evaluates a single record payload against its peer cohort distribution.
        """
        cohort_key = get_cohort_key(payload)
        stats = self.cohort_stats.get(cohort_key)

        # Fallback if cohort not seen or small cohort
        if not stats or stats["size"] < 3:
            return StatisticalResult(
                cohort_key=cohort_key,
                cohort_size=stats["size"] if stats else 0,
                anomaly_score=0.0,
                highest_z_score=0.0,
                outliers=[],
                evidence_bullets=[]
            )

        c_size = stats["size"]
        outliers: List[StatisticalOutlier] = []
        evidence_bullets: List[str] = []
        max_z = 0.0

        target_cols = ["Earnings_Last_Month", "Daily_Wages", "Monthly_Exp"]
        col_labels = {
            "Earnings_Last_Month": "Monthly Earnings",
            "Daily_Wages": "Daily Wage Rate",
            "Monthly_Exp": "Monthly Expenditure (MPCE)"
        }

        for col in target_cols:
            val = float(payload.get(col, 0.0) or 0.0)
            col_stat = stats["metrics"].get(col)
            if not col_stat:
                continue

            mean_val = col_stat["mean"]
            std_val = col_stat["std"]
            median_val = col_stat["median"]
            iqr_low = col_stat["iqr_low"]
            iqr_high = col_stat["iqr_high"]
            mad_val = col_stat["mad"]
            raw_vals = col_stat["raw_vals"]

            z_score = round(abs(val - mean_val) / std_val, 2)
            mad_score = round(abs(val - median_val) / mad_val, 2)
            is_iqr = bool(val < iqr_low or val > iqr_high)

            # Percentile rank
            pct = round(float(np.searchsorted(raw_vals, val) / len(raw_vals) * 100.0), 1)

            if z_score > max_z:
                max_z = z_score

            # Flag as statistical outlier if Z-score > 2.5 or IQR outlier with significant MAD
            if z_score >= 2.5 or is_iqr or mad_score >= 3.0:
                direction = "higher" if val > median_val else "lower"
                mult = round(val / max(1.0, median_val), 1) if val > median_val else round(median_val / max(1.0, val), 1)

                desc = f"{col_labels[col]} of INR {val:,.2f} is {mult}x {direction} than peer cohort median (INR {median_val:,.2f}), placed at {pct}th percentile (Z-score: {z_score})."

                outlier = StatisticalOutlier(
                    field=col,
                    value=val,
                    cohort_key=cohort_key,
                    cohort_size=c_size,
                    cohort_mean=mean_val,
                    cohort_median=median_val,
                    cohort_std=std_val,
                    cohort_iqr_low=iqr_low,
                    cohort_iqr_high=iqr_high,
                    z_score=z_score,
                    mad_score=mad_score,
                    percentile=pct,
                    is_iqr_outlier=is_iqr,
                    deviation_description=desc
                )
                outliers.append(outlier)
                evidence_bullets.append(desc)

        # Anomaly score normalized between 0.0 and 1.0 based on Z-score
        anomaly_score = round(min(1.0, max_z / 5.0), 3)

        return StatisticalResult(
            cohort_key=cohort_key,
            cohort_size=c_size,
            anomaly_score=anomaly_score,
            highest_z_score=max_z,
            outliers=outliers,
            evidence_bullets=evidence_bullets
        )
