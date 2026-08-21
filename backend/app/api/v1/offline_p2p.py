from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List
from app.db.session import get_db
from app.engines.rule_engine import RuleEngine
from app.engines.statistical_engine import StatisticalResult
from app.engines.ml_engine import MLResult
from app.engines.fusion_engine import FusionEngine
from app.engines.evidence_composer import EvidenceComposer

router = APIRouter(prefix="/p2p", tags=["Offline P2P Hotspot"])

class P2PBatchIngest(BaseModel):
  device_id: str
  survey_code: str = "PLFS_2024"
  records: List[Dict[str, Any]]

@router.post("/ingest")
def p2p_hotspot_ingest(payload: P2PBatchIngest, db: Session = Depends(get_db)):
    """
    Local Wi-Fi Hotspot P2P Microdata Ingestion Endpoint.
    Allows CAPI enumerator tablets to pair directly with a supervisor's field laptop in remote villages without cellular towers.
    """
    rule_engine = RuleEngine()
    processed = []

    from app.models.schema import ValidationRule
    rules = db.query(ValidationRule).all()

    for r in payload.records:
        val_res = rule_engine.validate_record(r, rules)
        processed.append({
            "record_id": r.get("id", "P2P_001"),
            "status": "INGESTED_P2P",
            "rule_violations": len(val_res.violations),
            "evaluated_offline": True
        })

    return {
        "status": "SUCCESS",
        "device_id": payload.device_id,
        "mode": "LOCAL_HOTSPOT_P2P",
        "records_received": len(payload.records),
        "results": processed
    }
