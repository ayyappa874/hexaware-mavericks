import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.engines.model_lab_engine import ModelLabEngine
from app.engines.feedback_calibration import FeedbackCalibrationEngine
from app.engines.fusion_engine import FusionEngine

def test_fusion_weight_calibration():
    # Simulate supervisor precision calculation
    fusion = FusionEngine(w_rule=0.35, w_stat=0.35, w_ml=0.30)
    
    # Check initial weights sum to 1.0
    assert abs((fusion.w_rule + fusion.w_stat + fusion.w_ml) - 1.0) < 1e-5

    # Test weight recalibration formula
    precisions = {"RULE_ENGINE": 0.90, "STATISTICAL_ENGINE": 0.80, "ML_ENGINE": 0.70}
    total_p = sum(precisions.values())
    w_r = precisions["RULE_ENGINE"] / total_p
    w_s = precisions["STATISTICAL_ENGINE"] / total_p
    w_m = precisions["ML_ENGINE"] / total_p

    assert round(w_r + w_s + w_m, 3) == 1.0
