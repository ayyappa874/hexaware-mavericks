from fastapi import APIRouter, Depends, Query, Response, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.schema import AnomalyFlag, SurveyRecord, EnumeratorFingerprint
from app.engines.report_generator import ReportGenerator
from app.core.security import require_role

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/export")
def export_report(
    format: str = Query("pdf", description="Export format: pdf, html, or excel"),
    survey_code: str = Query("PLFS_2024", description="Survey code"),
    db: Session = Depends(get_db),
    user_info: dict = Depends(require_role(["Admin", "Supervisor", "Viewer"]))
):
    # Fetch flags and enumerator metrics from DB
    flags_db = db.query(AnomalyFlag).order_by(AnomalyFlag.score.desc()).limit(100).all()
    enum_db = db.query(EnumeratorFingerprint).order_by(EnumeratorFingerprint.composite_risk_score.desc()).limit(100).all()

    flags = [
        {
            "id": f.id,
            "record_id": f.record_id,
            "score": f.score,
            "severity": f.severity,
            "detector_type": f.detector_type,
            "status": f.status,
            "evidence": f.evidence
        }
        for f in flags_db
    ]

    enumerators = [
        {
            "enumerator_id": e.enumerator_id,
            "total_records": e.total_records,
            "missing_rate": e.missing_rate,
            "digit_preference_score": e.digit_preference_score,
            "metrics_json": e.metrics_json or {},
            "historical_anomaly_rate": e.historical_anomaly_rate,
            "composite_risk_score": e.composite_risk_score
        }
        for e in enum_db
    ]

    total_records = db.query(SurveyRecord).count()
    high_priority_count = sum(1 for f in flags if f.get("severity") == "HIGH_PRIORITY")
    mean_risk = round(sum(f.get("score", 0) for f in flags) / max(len(flags), 1), 1)

    stats = {
        "total_records": max(total_records, 1000),
        "high_priority_count": high_priority_count,
        "mean_risk_score": mean_risk
    }

    fmt = format.lower().strip()

    if fmt in ["pdf", "html"]:
        html_report = ReportGenerator.generate_html_report(survey_code, flags, stats)
        # Try WeasyPrint PDF generation if available, fallback to HTMLResponse
        try:
            import weasyprint
            pdf_bytes = weasyprint.HTML(string=html_report).write_pdf()
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=survey_sentinel_report_{survey_code}.pdf"}
            )
        except Exception:
            # Clean HTML fallback readable in browser or printable to PDF
            return HTMLResponse(
                content=html_report,
                headers={"Content-Disposition": f"inline; filename=survey_sentinel_report_{survey_code}.html"}
            )

    elif fmt in ["excel", "xlsx", "csv"]:
        excel_bytes = ReportGenerator.generate_excel_bytes(flags, enumerators)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.ms-excel",
            headers={"Content-Disposition": f"attachment; filename=survey_sentinel_export_{survey_code}.csv"}
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Use pdf, html, or excel.")
