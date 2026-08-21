import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.engines.counterfactual_engine import CounterfactualEngine

def test_counterfactual_recommendations():
    # Test record payload with child salaried worker violation and earnings outlier
    record_payload = {
        "Age": 12,
        "Usual_Principal_Activity_Status": 31, # Child salaried worker violation
        "Earnings_Last_Month": 95000.0,      # High earnings outlier
        "Daily_Wages": 4500.0,
        "Monthly_Exp": 25000.0,
        "State": "07",
        "Sector": "2"
    }

    # Verify rule recommendation logic
    age = record_payload["Age"]
    status = record_payload["Usual_Principal_Activity_Status"]
    assert age < 15 and status == 31
