import sys
import os
import uuid
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.db.session import SessionLocal, engine
from app.models.schema import Base, Survey, SurveyRecord, ValidationRule, AnomalyFlag, AuditLog

def seed_large_dataset(target_count: int = 10000):
    print("=========================================================")
    print(f" SEEDING LARGE PLFS MICRODATA DATASET ({target_count} RECORDS)")
    print("=========================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Ensure Survey Record exists
    survey = db.query(Survey).filter(Survey.code == "PLFS_2024").first()
    if not survey:
        survey = Survey(
            id=str(uuid.uuid4()),
            code="PLFS_2024",
            name="Periodic Labour Force Survey 2024-25",
            version="1.0",
            schema_json={"fields": ["State", "District", "Sector", "Age", "Sex", "Earnings_Last_Month"]}
        )
        db.add(survey)
        db.commit()

    current_records = db.query(SurveyRecord).count()
    to_create = target_count - current_records

    if to_create <= 0:
        print(f"Database already contains {current_records} records. Target reached.")
        db.close()
        return

    print(f"Current records: {current_records}. Seeding {to_create} new records...")

    states = [f"{i:02d}" for i in range(1, 37)]
    sectors = [1, 2] # 1=Rural, 2=Urban
    statuses = [11, 21, 31, 41, 51, 81, 91, 92, 93, 97]
    rounds = ["2023-24", "2024-25"]
    enumerator_ids = [f"ENUM_{100 + i}" for i in range(50)]

    records_batch = []
    flags_batch = []
    now = datetime.utcnow()

    for i in range(to_create):
        rec_id = str(uuid.uuid4())
        rec_num = current_records + i + 1
        st = random.choice(states)
        dist = f"{random.randint(1, 30):03d}"
        sec = random.choice(sectors)
        rnd = random.choices(rounds, weights=[0.4, 0.6])[0]
        enum_id = random.choice(enumerator_ids)
        fsu = f"FSU_{st}{dist}_{random.randint(100, 999)}"

        age = random.randint(5, 80)
        status = random.choice(statuses)
        edu = random.randint(1, 14)
        sex = random.choice([1, 2])

        # Generate realistic earnings with occasional anomalies
        is_anomalous = random.random() < 0.12 # 12% anomaly rate
        if is_anomalous:
            earnings = float(random.choice([65000, 85000, 120000, 250000]))
            wages = float(random.choice([2500, 4500, 8000]))
            if age < 15:
                status = 31 # Salaried child
                edu = 12 # Graduate child
        else:
            earnings = float(random.randint(5000, 45000)) if status in [11, 31, 51] else 0.0
            wages = float(random.randint(200, 800)) if status in [41, 51] else 0.0

        payload = {
            "Survey_Round": rnd,
            "State": st,
            "District": dist,
            "Sector": sec,
            "Hh_No": random.randint(1, 50),
            "Person_No": random.randint(1, 8),
            "Rel_To_Head": 1 if i % 4 == 0 else random.randint(2, 6),
            "Sex": sex,
            "Age": age,
            "General_Edu": edu,
            "Usual_Principal_Activity_Status": status,
            "Earnings_Last_Month": earnings,
            "Daily_Wages": wages,
            "Monthly_Exp": float(random.randint(3000, 25000)),
            "Enumerator_ID": enum_id
        }

        created_time = now - timedelta(days=random.randint(0, 180), minutes=random.randint(0, 1440))

        rec = SurveyRecord(
            id=rec_id,
            survey_id=survey.id,
            survey_round=rnd,
            record_id=f"REC_PLFS_{rnd}_{st}{dist}_{rec_num:06d}",
            state_code=st,
            district_code=dist,
            sector=sec,
            fsu_id=fsu,
            raw_payload=payload,
            ingested_at=created_time
        )
        records_batch.append(rec)

        # Generate corresponding anomaly flags for high risk records
        if is_anomalous or earnings > 50000 or (age < 15 and status == 31):
            risk_score = random.randint(52, 98)
            sev = "HIGH_PRIORITY" if risk_score >= 75 else "REVIEW"
            detector = random.choice(["RuleEngine", "StatisticalEngine", "MLEngine", "BenfordEngine"])
            
            bullets = []
            if age < 15 and status == 31:
                bullets.append("RULE_MIN_AGE_SALARIED: Person age < 15 reported as regular salaried worker.")
            if earnings > 50000:
                bullets.append(f"Earnings ₹{earnings:,.0f} exceed peer cohort mean (Z-Score = +3.8).")
            if not bullets:
                bullets.append("Unsupervised Isolation Forest flagged high-dimensional multivariate anomaly.")

            flag = AnomalyFlag(
                id=str(uuid.uuid4()),
                record_id=rec.record_id,
                survey_id=survey.id,
                detector_type=detector,
                severity=sev,
                score=risk_score,
                evidence={
                    "risk_score": risk_score,
                    "severity": sev,
                    "narrative_bullets": bullets,
                    "rule_score": random.randint(40, 90),
                    "stat_score": random.randint(40, 90),
                    "ml_score": random.randint(40, 90)
                },
                status=random.choice(["PENDING", "PENDING", "CONFIRMED", "DISMISSED"]),
                created_at=created_time
            )
            flags_batch.append(flag)

        # Batch insert every 1000 items
        if len(records_batch) >= 1000:
            db.bulk_save_objects(records_batch)
            if flags_batch:
                db.bulk_save_objects(flags_batch)
            db.commit()
            print(f"Inserted batch... Total: {current_records + len(records_batch)}")
            records_batch = []
            flags_batch = []

    if records_batch:
        db.bulk_save_objects(records_batch)
        if flags_batch:
            db.bulk_save_objects(flags_batch)
        db.commit()

    total_final = db.query(SurveyRecord).count()
    total_flags = db.query(AnomalyFlag).count()
    print("=========================================================")
    print(f" SUCCESS! Seeded dataset complete.")
    print(f" Total Records in Database: {total_final}")
    print(f" Total Anomaly Flags in Database: {total_flags}")
    print("=========================================================")
    db.close()

if __name__ == "__main__":
    seed_large_dataset(10000)
