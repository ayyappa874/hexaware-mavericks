import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.schema import SurveyRecord

logger = logging.getLogger(__name__)

# MoSPI PLFS Usual Principal Activity Status Codes
EMPLOYED_CODES = [11, 12, 21, 31, 41, 51]
UNEMPLOYED_CODES = [81]
LABOUR_FORCE_CODES = EMPLOYED_CODES + UNEMPLOYED_CODES

class TemporalDriftEngine:
    """
    Temporal Drift Engine for Survey Sentinel.
    Computes official MoSPI LFPR, WPR, and Unemployment Rate indicators per State/District per Round,
    and detects statistically significant shifts across rounds.
    """

    @staticmethod
    def compute_round_indicators(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Computes weighted MoSPI LFPR, WPR, and UR indicators from raw PLFS microdata payloads.
        Returns dictionary keyed by State code -> {LFPR, WPR, UR, Total_Weighted_Pop, Sample_Count}.
        """
        if not records:
            return {}

        df = pd.DataFrame(records)
        
        # Parse fields cleanly
        df["State"] = df["State"].astype(str).str.zfill(2)
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce").fillna(0)
        df["Activity"] = pd.to_numeric(df["Usual_Principal_Activity_Status"], errors="coerce").fillna(0)
        df["Weight"] = pd.to_numeric(df["Multiplier"], errors="coerce").fillna(1.0)

        # Filter population 15+ years per MoSPI PLFS standards
        df_15plus = df[df["Age"] >= 15].copy()

        state_indicators = {}
        grouped = df_15plus.groupby("State")

        for state_code, group in grouped:
            sample_cnt = len(group)
            total_weight_pop = float(group["Weight"].sum())

            if total_weight_pop <= 0:
                continue

            # Weighted counts
            employed_w = float(group[group["Activity"].isin(EMPLOYED_CODES)]["Weight"].sum())
            unemployed_w = float(group[group["Activity"].isin(UNEMPLOYED_CODES)]["Weight"].sum())
            labour_force_w = float(group[group["Activity"].isin(LABOUR_FORCE_CODES)]["Weight"].sum())

            # 1. LFPR: % of 15+ population in Labour Force
            lfpr = round((labour_force_w / total_weight_pop) * 100.0, 2)

            # 2. WPR: % of 15+ population Employed
            wpr = round((employed_w / total_weight_pop) * 100.0, 2)

            # 3. Unemployment Rate (UR): % of Labour Force Unemployed
            ur = round((unemployed_w / max(1.0, labour_force_w)) * 100.0, 2)

            state_indicators[state_code] = {
                "lfpr": lfpr,
                "wpr": wpr,
                "ur": ur,
                "employed_weighted": round(employed_w, 2),
                "unemployed_weighted": round(unemployed_w, 2),
                "labour_force_weighted": round(labour_force_w, 2),
                "total_population_weighted": round(total_weight_pop, 2),
                "sample_count": sample_cnt
            }

        return state_indicators

    @staticmethod
    def detect_temporal_drift(db: Session, survey_id: str, state_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates round-over-round indicator drift between baseline (2023-24) and current (2024-25) rounds,
        flagging statistically significant deviations.
        """
        all_recs = db.query(SurveyRecord).filter(SurveyRecord.survey_id == survey_id).all()
        if not all_recs:
            return {"status": "no_data", "states": {}}

        payloads_by_round: Dict[str, List[Dict[str, Any]]] = {}
        for r in all_recs:
            s_round = r.survey_round or "2023-24"
            if isinstance(r.raw_payload, dict):
                payloads_by_round.setdefault(s_round, []).append(r.raw_payload)

        rounds = sorted(payloads_by_round.keys())
        if len(rounds) < 2:
            # Single round case
            curr_round = rounds[0]
            curr_indicators = TemporalDriftEngine.compute_round_indicators(payloads_by_round[curr_round])
            return {
                "status": "single_round",
                "rounds_available": rounds,
                "current_round": curr_round,
                "state_data": curr_indicators,
                "drift_flags": []
            }

        baseline_round = rounds[0]
        current_round = rounds[-1]

        base_indicators = TemporalDriftEngine.compute_round_indicators(payloads_by_round[baseline_round])
        curr_indicators = TemporalDriftEngine.compute_round_indicators(payloads_by_round[current_round])

        # Filter by state if requested
        states_to_evaluate = [state_code.zfill(2)] if state_code else sorted(set(base_indicators.keys()).union(set(curr_indicators.keys())))

        # Compute historical standard deviation across baseline indicator values for significance test
        base_lfprs = [v["lfpr"] for v in base_indicators.values()]
        base_wprs = [v["wpr"] for v in base_indicators.values()]
        base_urs = [v["ur"] for v in base_indicators.values()]

        std_lfpr = max(1.5, float(np.std(base_lfprs))) if base_lfprs else 2.0
        std_wpr = max(1.5, float(np.std(base_wprs))) if base_wprs else 2.0
        std_ur = max(1.5, float(np.std(base_urs))) if base_urs else 2.0

        drift_analysis = []
        drift_flags = []

        for st in states_to_evaluate:
            b_data = base_indicators.get(st, {"lfpr": 0.0, "wpr": 0.0, "ur": 0.0, "sample_count": 0})
            c_data = curr_indicators.get(st, {"lfpr": 0.0, "wpr": 0.0, "ur": 0.0, "sample_count": 0})

            diff_lfpr = round(c_data["lfpr"] - b_data["lfpr"], 2)
            diff_wpr = round(c_data["wpr"] - b_data["wpr"], 2)
            diff_ur = round(c_data["ur"] - b_data["ur"], 2)

            z_lfpr = round(diff_lfpr / std_lfpr, 2)
            z_wpr = round(diff_wpr / std_wpr, 2)
            z_ur = round(diff_ur / std_ur, 2)

            # Flag statistically significant drift if |Z| >= 2.0
            is_sig_lfpr = bool(abs(z_lfpr) >= 2.0)
            is_sig_wpr = bool(abs(z_wpr) >= 2.0)
            is_sig_ur = bool(abs(z_ur) >= 2.0)

            st_summary = {
                "state_code": st,
                "baseline_round": baseline_round,
                "current_round": current_round,
                "indicators": {
                    "lfpr": {"baseline": b_data["lfpr"], "current": c_data["lfpr"], "delta": diff_lfpr, "z_score": z_lfpr, "is_statistically_significant": is_sig_lfpr},
                    "wpr": {"baseline": b_data["wpr"], "current": c_data["wpr"], "delta": diff_wpr, "z_score": z_wpr, "is_statistically_significant": is_sig_wpr},
                    "ur": {"baseline": b_data["ur"], "current": c_data["ur"], "delta": diff_ur, "z_score": z_ur, "is_statistically_significant": is_sig_ur}
                },
                "baseline_sample_size": b_data["sample_count"],
                "current_sample_size": c_data["sample_count"]
            }
            drift_analysis.append(st_summary)

            if is_sig_lfpr or is_sig_wpr or is_sig_ur:
                drift_flags.append({
                    "state_code": st,
                    "reason": f"Statistically significant shift detected in State {st}: LFPR delta={diff_lfpr}% (Z={z_lfpr}), WPR delta={diff_wpr}% (Z={z_wpr}), UR delta={diff_ur}% (Z={z_ur})."
                })

        return {
            "status": "success",
            "baseline_round": baseline_round,
            "current_round": current_round,
            "states_evaluated": len(drift_analysis),
            "drift_analysis": drift_analysis,
            "significant_drift_flags": drift_flags
        }
