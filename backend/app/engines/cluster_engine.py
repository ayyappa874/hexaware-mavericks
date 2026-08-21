from typing import List, Dict, Any
from collections import defaultdict

class ClusterEngine:
    """
    Groups anomaly flags into semantic root cause clusters based on shared attributes
    (e.g., same district + field anomaly, FSU digit preference, logical rule violations).
    """

    @staticmethod
    def cluster_flags(flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clusters_map = defaultdict(list)

        for flag in flags:
            detector = flag.get("detector_type", "Fusion")
            severity = flag.get("severity", "MEDIUM")
            evidence = flag.get("evidence", {})
            bullets = evidence.get("narrative_bullets", [])
            bullets_text = " ".join(bullets).lower()

            # Rule violation cluster
            if "rule" in detector.lower() or "violated" in bullets_text or "child" in bullets_text:
                cluster_key = "Child & Labour Rule Consistency Violations"
            # Digit preference cluster
            elif "digit" in bullets_text or "clustering" in bullets_text or "fsu" in bullets_text:
                cluster_key = "FSU Digit Preference & Excess Zero Clustering"
            # High wage / earnings outlier cluster
            elif "earning" in bullets_text or "wage" in bullets_text or "z-score" in bullets_text:
                cluster_key = "Extreme Earnings Cohort Outliers"
            # Temporal drift cluster
            elif "temporal" in bullets_text or "shift" in bullets_text:
                cluster_key = "District Temporal Indicator Shift Outliers"
            else:
                cluster_key = "Multivariate Peer Cohort Isolation Outliers"

            clusters_map[cluster_key].append(flag)

        result_clusters = []
        for name, cluster_flags in clusters_map.items():
            scores = [f.get("score", 50.0) for f in cluster_flags]
            avg_score = round(sum(scores) / max(len(scores), 1), 1)

            # Extract sample evidence narrative
            sample_bullet = "Multiple multi-detector anomalies detected in this cohort."
            for f in cluster_flags:
                bullets = f.get("evidence", {}).get("narrative_bullets", [])
                if bullets:
                    sample_bullet = bullets[0]
                    break

            result_clusters.append({
                "cluster_name": name,
                "record_count": len(cluster_flags),
                "avg_risk_score": avg_score,
                "primary_detector": cluster_flags[0].get("detector_type", "Fusion") if cluster_flags else "Fusion",
                "sample_evidence": sample_bullet,
                "records": [
                    {
                        "id": f.get("id"),
                        "record_id": f.get("record_id"),
                        "score": f.get("score"),
                        "severity": f.get("severity")
                    }
                    for f in cluster_flags[:10]
                ]
            })

        # Sort clusters by record count descending
        result_clusters.sort(key=lambda x: x["record_count"], reverse=True)
        return result_clusters
