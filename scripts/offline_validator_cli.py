#!/usr/bin/env python3
"""
Survey Sentinel — Standalone Offline Laptop Validation CLI
Runnable directly on government laptops from a USB thumbdrive without internet or backend server dependencies.
"""

import sys
import os
import csv
import json
import argparse
from datetime import datetime

# Standalone Rule Evaluator
def evaluate_record_offline(row: dict) -> dict:
    violations = []
    rule_score = 0

    age = int(float(row.get("Age", 0) or 0))
    status = int(float(row.get("Usual_Principal_Activity_Status", 0) or 0))
    earnings = float(row.get("Earnings_Last_Month", 0) or 0)
    edu = int(float(row.get("General_Edu", 0) or 0))
    wages = float(row.get("Daily_Wages", 0) or 0))

    if edu >= 8 and age < 18:
        violations.append("RULE_MIN_AGE_GRADUATE: Age < 18 with Graduate degree.")
        rule_score += 35

    if status in [31, 41, 51] and age < 14:
        violations.append("RULE_MIN_AGE_SALARIED: Age < 14 reported as regular salaried worker.")
        rule_score += 40

    if status >= 91 and earnings > 20000:
        violations.append(f"RULE_STUDENT_HIGH_EARNINGS: Inactive status code reported ₹{earnings} earnings.")
        rule_score += 30

    if wages > 15000:
        violations.append(f"RULE_CASUAL_WAGE_LIMIT: Daily wage ₹{wages} exceeds maximum threshold.")
        rule_score += 25

    rule_score = min(rule_score, 100)

    # Statistical Cohort Z-Score (State 07 Urban Adult Salaried Worker Mean = ₹22,500, Std = ₹14,000)
    stat_score = 0
    if earnings > 0:
        z = (earnings - 22500.0) / 14000.0
        if z > 2.5:
            violations.append(f"Earnings ₹{earnings} exceed peer cohort mean (Z-Score = +{round(z, 2)}).")
        stat_score = min(max(int((z / 4.0) * 100), 0), 100)

    overall_risk = int(0.6 * rule_score + 0.4 * stat_score)
    severity = "HIGH_PRIORITY" if overall_risk >= 75 else "REVIEW" if overall_risk >= 50 else "MONITOR" if overall_risk >= 30 else "NORMAL"

    return {
        "record_id": row.get("id") or row.get("Record_ID") or f"REC_{hash(str(row)) & 0xFFFFFFFF}",
        "overall_risk": overall_risk,
        "severity": severity,
        "violations": violations,
        "evaluated_at": datetime.now().isoformat()
    }

def main():
    parser = argparse.ArgumentParser(description="Survey Sentinel — Standalone Offline Laptop Validation CLI")
    parser.add_argument("--input", required=True, help="Path to input PLFS microdata CSV file")
    parser.add_argument("--output", default="offline_validation_report.json", help="Output JSON report file path")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    print("=========================================================")
    print(" SURVEY SENTINEL — STANDALONE OFFLINE VALIDATOR CLI")
    print("=========================================================")
    print(f"Ingesting microdata file: {args.input}")

    records_processed = 0
    anomalies_flagged = 0
    results = []

    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records_processed += 1
            res = evaluate_record_offline(row)
            if res["overall_risk"] >= 30:
                anomalies_flagged += 1
            results.append(res)

    high_priority = [r for r in results if r["severity"] == "HIGH_PRIORITY"]

    report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": args.input,
        "total_records_processed": records_processed,
        "anomalies_flagged": anomalies_flagged,
        "high_priority_count": len(high_priority),
        "results": results[:100]
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Validation complete!")
    print(f"Processed: {records_processed} records")
    print(f"Anomalies Flagged: {anomalies_flagged} (High Priority: {len(high_priority)})")
    print(f"Saved offline report to: {args.output}")
    print("=========================================================")

if __name__ == "__main__":
    main()
