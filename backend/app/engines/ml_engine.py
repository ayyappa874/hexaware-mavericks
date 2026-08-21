import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from app.engines.statistical_engine import get_cohort_key

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "Age",
    "Earnings_Last_Month",
    "Daily_Wages",
    "Monthly_Exp",
    "Usual_Principal_Activity_Status",
    "General_Edu",
    "Multiplier"
]

class MLResult(BaseModel):
    cohort_key: str
    iforest_score: float # 0.0 (normal) to 1.0 (outlier)
    lof_score: float # 0.0 (normal) to 1.0 (outlier)
    combined_ml_score: float # 0.0 to 1.0
    is_anomaly: bool
    top_contributing_features: List[str]
    evidence_bullets: List[str]

class MLEngine:
    """
    ML Anomaly Detector for Survey Sentinel.
    Runs Isolation Forest and Local Outlier Factor (LOF) per peer cohort.
    """

    def __init__(self):
        self.cohort_iforest: Dict[str, IsolationForest] = {}
        self.cohort_lof: Dict[str, LocalOutlierFactor] = {}
        self.cohort_means: Dict[str, np.ndarray] = {}

    def extract_features(self, payload: Dict[str, Any]) -> np.ndarray:
        row = []
        for col in FEATURE_COLUMNS:
            val = payload.get(col, 0.0)
            try:
                row.append(float(val) if val is not None else 0.0)
            except (ValueError, TypeError):
                row.append(0.0)
        return np.array(row, dtype=np.float64)

    def fit(self, records: List[Dict[str, Any]]):
        """
        Trains IsolationForest and LOF models per peer cohort.
        """
        if not records:
            return

        df = pd.DataFrame(records)
        df["cohort_key"] = df.apply(get_cohort_key, axis=1)

        grouped = df.groupby("cohort_key")
        self.cohort_iforest = {}
        self.cohort_lof = {}
        self.cohort_means = {}

        for cohort_key, group in grouped:
            if len(group) < 5:
                continue # Need minimum samples to train robust ML models

            feature_matrix = []
            for _, row in group.iterrows():
                feat = self.extract_features(row.to_dict())
                feature_matrix.append(feat)

            X = np.array(feature_matrix)
            self.cohort_means[cohort_key] = np.mean(X, axis=0)

            # Fit Isolation Forest
            iforest = IsolationForest(
                n_estimators=50,
                contamination=0.05,
                random_state=42
            )
            iforest.fit(X)
            self.cohort_iforest[cohort_key] = iforest

            # Fit LOF (novelty=True for prediction)
            lof = LocalOutlierFactor(
                n_neighbors=min(15, len(group) - 1),
                contamination=0.05,
                novelty=True
            )
            lof.fit(X)
            self.cohort_lof[cohort_key] = lof

        logger.info(f"Fitted MLEngine (IsolationForest + LOF) across {len(self.cohort_iforest)} peer cohorts.")

    def evaluate_record(self, payload: Dict[str, Any]) -> MLResult:
        """
        Evaluates a single record against trained ML models for its cohort.
        """
        cohort_key = get_cohort_key(payload)
        iforest = self.cohort_iforest.get(cohort_key)
        lof = self.cohort_lof.get(cohort_key)

        if not iforest or not lof:
            return MLResult(
                cohort_key=cohort_key,
                iforest_score=0.0,
                lof_score=0.0,
                combined_ml_score=0.0,
                is_anomaly=False,
                top_contributing_features=[],
                evidence_bullets=[]
            )

        X_input = self.extract_features(payload).reshape(1, -1)

        # 1. Isolation Forest score (-1.0 to +1.0, lower means outlier)
        if_raw_score = iforest.score_samples(X_input)[0]
        # Normalize: raw scores typically range from -0.8 (outlier) to -0.3 (normal)
        if_norm = float(np.clip((0.0 - if_raw_score) * 2.0, 0.0, 1.0))

        # 2. LOF score
        lof_raw_score = lof.score_samples(X_input)[0]
        lof_norm = float(np.clip((-1.5 - lof_raw_score) * 1.5, 0.0, 1.0))

        combined_ml_score = round(0.55 * if_norm + 0.45 * lof_norm, 3)

        # Contributing feature calculation
        mean_feat = self.cohort_means[cohort_key]
        abs_diffs = np.abs(X_input[0] - mean_feat)
        top_indices = np.argsort(abs_diffs)[::-1][:2]

        top_features = [FEATURE_COLUMNS[i] for i in top_indices if abs_diffs[i] > 1e-3]

        evidence_bullets = []
        is_anomaly = combined_ml_score >= 0.50

        if is_anomaly:
            bullets = [
                f"Isolation Forest detector identified multivariate anomaly pattern in peer cohort (ML Anomaly Score: {combined_ml_score:.2f}).",
                f"Primary contributing dimensions: {', '.join(top_features)}."
            ]
            evidence_bullets.extend(bullets)

        return MLResult(
            cohort_key=cohort_key,
            iforest_score=round(if_norm, 3),
            lof_score=round(lof_norm, 3),
            combined_ml_score=combined_ml_score,
            is_anomaly=is_anomaly,
            top_contributing_features=top_features,
            evidence_bullets=evidence_bullets
        )
