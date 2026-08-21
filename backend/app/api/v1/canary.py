from fastapi import APIRouter
from app.engines.canary_engine import CanaryEngine

router = APIRouter(prefix="/canary", tags=["Canary Self-Audit"])

@router.get("/detection-rate")
def get_canary_detection_rate(window: str = "30d"):
    """
    Returns empirical Red-Team Canary self-audit detection rate metrics.
    """
    return CanaryEngine.evaluate_canary_run()
