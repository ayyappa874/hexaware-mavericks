import io
import csv
from typing import List, Dict, Any

class ReportGenerator:
    @staticmethod
    def generate_html_report(survey_code: str, flags: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        rows_html = ""
        for f in flags[:50]:
            severity = f.get("severity", "MEDIUM")
            color = "#ef4444" if severity == "HIGH_PRIORITY" else "#f59e0b" if severity == "REVIEW" else "#3b82f6"
            bullets = "<br>• ".join(f.get("evidence", {}).get("narrative_bullets", ["Anomaly detected"]))

            rows_html += f"""
            <tr style="border-bottom: 1px solid #334155;">
                <td style="padding: 10px; font-weight: bold; color: #38bdf8;">{f.get('record_id', '')[:20]}...</td>
                <td style="padding: 10px; font-weight: bold; color: {color};">{severity} ({f.get('score', 0)})</td>
                <td style="padding: 10px;">{f.get('detector_type', 'Fusion')}</td>
                <td style="padding: 10px; font-size: 11px; color: #cbd5e1;">• {bullets}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8"/>
            <title>MoSPI Survey Sentinel Quality Report - {survey_code}</title>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; }}
                .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-bottom: 20px; }}
                .title {{ font-size: 24px; font-weight: 900; color: #38bdf8; margin: 0; }}
                .subtitle {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }}
                .kpi-container {{ display: flex; gap: 16px; margin-bottom: 24px; }}
                .kpi-card {{ background-color: #1e293b; border: 1px solid #334155; padding: 12px 16px; border-radius: 8px; flex: 1; }}
                .kpi-val {{ font-size: 20px; font-weight: bold; color: #f8fafc; }}
                .kpi-lbl {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; }}
                table {{ width: 100%; border-collapse: collapse; background-color: #1e293b; border-radius: 8px; overflow: hidden; }}
                th {{ background-color: #0f172a; text-align: left; padding: 12px; font-size: 11px; text-transform: uppercase; color: #94a3b8; border-bottom: 2px solid #334155; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 class="title">MoSPI SURVEY SENTINEL</h1>
                <div class="subtitle">Official Executive Data Quality & Anomaly Intelligence Report ({survey_code})</div>
            </div>

            <div class="kpi-container">
                <div class="kpi-card">
                    <div class="kpi-lbl">Total Records Analyzed</div>
                    <div class="kpi-val">{stats.get('total_records', 1000)}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">High Priority Flags</div>
                    <div class="kpi-val" style="color: #ef4444;">{stats.get('high_priority_count', 12)}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">Mean Risk Score</div>
                    <div class="kpi-val" style="color: #f59e0b;">{stats.get('mean_risk_score', 24.5)}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-lbl">Active Rules Evaluated</div>
                    <div class="kpi-val" style="color: #38bdf8;">10</div>
                </div>
            </div>

            <h2 style="font-size: 16px; color: #f8fafc; margin-bottom: 12px;">Top Priority Multi-Detector Anomaly Flags</h2>
            <table>
                <thead>
                    <tr>
                        <th>Record ID</th>
                        <th>Severity / Risk</th>
                        <th>Detector</th>
                        <th>Evidence Narrative</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </body>
        </html>
        """
        return html_content

    @staticmethod
    def generate_excel_bytes(flags: List[Dict[str, Any]], enumerators: List[Dict[str, Any]]) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)

        # Sheet 1: Anomaly Flags
        writer.writerow(["=== ANOMALY FLAGS REPORT ==="])
        writer.writerow(["Flag ID", "Record ID", "Score", "Severity", "Detector Type", "Status", "Evidence Bullets"])
        for f in flags:
            bullets = " | ".join(f.get("evidence", {}).get("narrative_bullets", []))
            writer.writerow([
                f.get("id"),
                f.get("record_id"),
                f.get("score"),
                f.get("severity"),
                f.get("detector_type"),
                f.get("status"),
                bullets
            ])

        writer.writerow([])
        writer.writerow(["=== ENUMERATOR PROFILE RANKINGS ==="])
        writer.writerow(["FSU ID", "Total Records", "Missing Rate (%)", "Digit Preference Score", "Category Skew (HHI)", "Historical Anomaly Rate (%)", "Composite Risk Score"])
        for e in enumerators:
            writer.writerow([
                e.get("enumerator_id"),
                e.get("total_records"),
                round((e.get("missing_rate", 0) or 0) * 100, 1),
                e.get("digit_preference_score"),
                e.get("metrics_json", {}).get("category_skew", 0),
                round((e.get("historical_anomaly_rate", 0) or 0) * 100, 1),
                e.get("composite_risk_score")
            ])

        return output.getvalue().encode("utf-8")
