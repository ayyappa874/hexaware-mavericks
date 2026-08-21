import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.schema import SurveyRecord, AnomalyFlag, EnumeratorFingerprint

logger = logging.getLogger(__name__)

def calculate_digit_preference(values: List[float]) -> float:
    """
    Calculates last-digit preference score (0.0 to 1.0) on numeric survey responses.
    High score indicates heavy rounding / digit clustering (e.g. 50000, 10000, 500).
    """
    if not values:
        return 0.0

    valid_vals = [v for v in values if v > 0]
    if not valid_vals:
        return 0.0

    rounded_hundreds = sum(1 for v in valid_vals if v % 100 == 0)
    rounded_thousands = sum(1 for v in valid_vals if v % 1000 == 0)

    ratio_hundreds = rounded_hundreds / len(valid_vals)
    ratio_thousands = rounded_thousands / len(valid_vals)

    # Weighted digit preference score
    score = round(min(1.0, 0.4 * ratio_hundreds + 0.6 * ratio_thousands), 3)
    return score

def calculate_category_hhi(categories: List[Any]) -> float:
    """
    Calculates Herfindahl-Hirschman Index (HHI) for categorical responses.
    High HHI (close to 1.0) indicates single category copy-paste skew.
    """
    if not categories:
        return 0.0
    series = pd.Series(categories)
    counts = series.value_counts(normalize=True)
    hhi = float(np.sum(counts ** 2))
    return round(hhi, 3)

class EnumeratorEngine:
    """
    Enumerator & FSU Profiling Engine for Survey Sentinel.
    Computes missing-value rate, digit preference, category skew, and historical anomaly rate.
    """

    @staticmethod
    def compute_and_store_fingerprints(db: Session, survey_id: str) -> List[Dict[str, Any]]:
        """
        Aggregates all survey records by FSU / Enumerator, computes fingerprint metrics,
        and saves/updates entries in 'enumerator_fingerprints' table.
        """
        records = db.query(SurveyRecord).filter(SurveyRecord.survey_id == survey_id).all()
        if not records:
            logger.warning("No survey records found to compute enumerator fingerprints.")
            return []

        # Map flagged record IDs for anomaly rate calculation
        flagged_rec_ids = set(
            f.record_id for f in db.query(AnomalyFlag.record_id).filter(AnomalyFlag.survey_id == survey_id).all()
        )

        # Group records by fsu_id
        fsu_groups: Dict[str, List[SurveyRecord]] = {}
        for r in records:
            fsu = r.fsu_id or "FSU_UNKNOWN"
            fsu_groups.setdefault(fsu, []).append(r)

        fingerprint_results = []
        raw_metrics = []

        for fsu_id, group_recs in fsu_groups.items():
            total_recs = len(group_recs)
            payloads = [r.raw_payload for r in group_recs if isinstance(r.raw_payload, dict)]

            # 1. Missing Value Rate
            missing_counts = 0
            total_fields = 0
            for p in payloads:
                for col in ["Age", "Sex", "General_Edu", "Usual_Principal_Activity_Status", "Earnings_Last_Month", "Daily_Wages", "Monthly_Exp"]:
                    total_fields += 1
                    val = p.get(col)
                    if val is None or val == "" or val == 0:
                        missing_counts += 1

            missing_rate = round(missing_counts / max(1, total_fields), 3)

            # 2. Digit Preference Score on numeric fields
            numeric_vals = []
            for p in payloads:
                for col in ["Earnings_Last_Month", "Daily_Wages", "Monthly_Exp"]:
                    try:
                        val = float(p.get(col, 0.0) or 0.0)
                        if val > 0:
                            numeric_vals.append(val)
                    except (ValueError, TypeError):
                        pass

            digit_pref_score = calculate_digit_preference(numeric_vals)

            # 3. Category Skew (HHI) on Usual_Principal_Activity_Status
            activities = [p.get("Usual_Principal_Activity_Status") for p in payloads if "Usual_Principal_Activity_Status" in p]
            category_skew = calculate_category_hhi(activities)

            # 4. Historical Anomaly Rate
            flagged_count = sum(1 for r in group_recs if r.id in flagged_rec_ids)
            anomaly_rate = round(flagged_count / max(1, total_recs), 3)

            raw_metrics.append({
                "fsu_id": fsu_id,
                "total_records": total_recs,
                "missing_rate": missing_rate,
                "digit_preference_score": digit_pref_score,
                "category_skew": category_skew,
                "historical_anomaly_rate": anomaly_rate,
                "group_recs": group_recs
            })

        # Calculate composite risk score via Z-score normalization across all FSUs
        if raw_metrics:
            df_m = pd.DataFrame(raw_metrics)
            
            # Means and STDs for normalization
            m_miss, s_miss = df_m["missing_rate"].mean(), df_m["missing_rate"].std() or 1.0
            m_dig, s_dig = df_m["digit_preference_score"].mean(), df_m["digit_preference_score"].std() or 1.0
            m_hhi, s_hhi = df_m["category_skew"].mean(), df_m["category_skew"].std() or 1.0
            m_anom, s_anom = df_m["historical_anomaly_rate"].mean(), df_m["historical_anomaly_rate"].std() or 1.0

            for item in raw_metrics:
                z_miss = (item["missing_rate"] - m_miss) / s_miss
                z_dig = (item["digit_preference_score"] - m_dig) / s_dig
                z_hhi = (item["category_skew"] - m_hhi) / s_hhi
                z_anom = (item["historical_anomaly_rate"] - m_anom) / s_anom

                # Weighted Composite Z-score (scaled 0 to 100)
                raw_z_sum = (0.20 * z_miss) + (0.30 * z_dig) + (0.20 * z_hhi) + (0.30 * z_anom)
                composite_score = round(min(100.0, max(0.0, 50.0 + (raw_z_sum * 15.0))), 1)
                item["composite_risk_score"] = composite_score

                # Save / update in database
                existing_fp = db.query(EnumeratorFingerprint).filter(
                    EnumeratorFingerprint.survey_id == survey_id,
                    EnumeratorFingerprint.enumerator_id == item["fsu_id"]
                ).first()

                metrics_json = {
                    "missing_rate": item["missing_rate"],
                    "digit_preference_score": item["digit_preference_score"],
                    "category_skew": item["category_skew"],
                    "historical_anomaly_rate": item["historical_anomaly_rate"],
                    "z_scores": {
                        "missing": round(float(z_miss), 2),
                        "digit": round(float(z_dig), 2),
                        "skew": round(float(z_hhi), 2),
                        "anomaly": round(float(z_anom), 2)
                    }
                }

                if not existing_fp:
                    fp = EnumeratorFingerprint(
                        survey_id=survey_id,
                        enumerator_id=item["fsu_id"],
                        total_records=item["total_records"],
                        missing_rate=item["missing_rate"],
                        digit_preference_score=item["digit_preference_score"],
                        historical_anomaly_rate=item["historical_anomaly_rate"],
                        composite_risk_score=item["composite_risk_score"],
                        metrics_json=metrics_json
                    )
                    db.add(fp)
                else:
                    existing_fp.total_records = item["total_records"]
                    existing_fp.missing_rate = item["missing_rate"]
                    existing_fp.digit_preference_score = item["digit_preference_score"]
                    existing_fp.historical_anomaly_rate = item["historical_anomaly_rate"]
                    existing_fp.composite_risk_score = item["composite_risk_score"]
                    existing_fp.metrics_json = metrics_json

                fingerprint_results.append({
                    "enumerator_id": item["fsu_id"],
                    "total_records": item["total_records"],
                    "missing_rate": item["missing_rate"],
                    "digit_preference_score": item["digit_preference_score"],
                    "category_skew": item["category_skew"],
                    "historical_anomaly_rate": item["historical_anomaly_rate"],
                    "composite_risk_score": item["composite_risk_score"],
                    "metrics_json": metrics_json
                })

            db.commit()
            logger.info(f"Updated enumerator fingerprints for {len(fingerprint_results)} FSUs in database.")

        return fingerprint_results
