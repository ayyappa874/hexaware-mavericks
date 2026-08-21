from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schema import AnomalyFlag
from app.engines.cluster_engine import ClusterEngine

router = APIRouter()

@router.get("/clusters")
def get_anomaly_clusters(db: Session = Depends(get_db)):
    """
    Groups current anomaly flags into semantic root cause clusters with record counts.
    """
    flags_db = db.query(AnomalyFlag).order_by(AnomalyFlag.score.desc()).limit(200).all()

    flags = [
        {
            "id": f.id,
            "record_id": f.record_id,
            "score": f.score,
            "severity": f.severity,
            "detector_type": f.detector_type,
            "status": f.status,
            "evidence": f.evidence or {}
        }
        for f in flags_db
    ]

    clusters = ClusterEngine.cluster_flags(flags)
    return {
        "total_flags_analyzed": len(flags),
        "total_clusters": len(clusters),
        "clusters": clusters
    }
