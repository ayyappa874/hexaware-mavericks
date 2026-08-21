import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.engines.enumerator_engine import calculate_digit_preference, calculate_category_hhi, EnumeratorEngine
from app.engines.temporal_engine import TemporalDriftEngine

def test_digit_preference_score():
    # Numbers with high rounding (1000, 5000, 20000)
    rounded_numbers = [5000.0, 10000.0, 15000.0, 20000.0, 25000.0]
    score_high = calculate_digit_preference(rounded_numbers)
    assert score_high == 1.0

    # Organic numbers (341.20, 1289.45, 87.12)
    organic_numbers = [341.20, 1289.45, 87.12, 451.90, 783.10]
    score_low = calculate_digit_preference(organic_numbers)
    assert score_low == 0.0

def test_category_hhi():
    # Extreme single category copy-paste skew
    skewed = [11, 11, 11, 11, 11, 11, 11, 11, 11, 11]
    hhi_skewed = calculate_category_hhi(skewed)
    assert hhi_skewed == 1.0

    # Balanced categories
    balanced = [11, 12, 21, 31, 41, 51, 81, 91, 92, 97]
    hhi_balanced = calculate_category_hhi(balanced)
    assert hhi_balanced < 0.20

def test_mospi_indicator_formulas():
    # Sample 10 population records for State 09
    sample_records = [
        {"State": "09", "Age": 30, "Usual_Principal_Activity_Status": 31, "Multiplier": 100.0}, # Employed
        {"State": "09", "Age": 28, "Usual_Principal_Activity_Status": 11, "Multiplier": 100.0}, # Employed
        {"State": "09", "Age": 22, "Usual_Principal_Activity_Status": 81, "Multiplier": 100.0}, # Unemployed
        {"State": "09", "Age": 24, "Usual_Principal_Activity_Status": 91, "Multiplier": 100.0}, # Inactive Domestic
        {"State": "09", "Age": 10, "Usual_Principal_Activity_Status": 97, "Multiplier": 100.0}, # Under 15 (ignored)
    ]

    indicators = TemporalDriftEngine.compute_round_indicators(sample_records)
    st_09 = indicators["09"]

    # 4 persons >= 15 yrs. Total weight = 400.
    # Labour Force = 3 (2 Employed + 1 Unemployed). Weight = 300.
    # Employed = 2. Weight = 200.
    # LFPR = 300 / 400 * 100 = 75.0%
    # WPR = 200 / 400 * 100 = 50.0%
    # UR = 100 / 300 * 100 = 33.33%

    assert st_09["lfpr"] == 75.0
    assert st_09["wpr"] == 50.0
    assert st_09["ur"] == 33.33
