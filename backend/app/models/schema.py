import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False, index=True) # e.g. PLFS_2024
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    schema_definition = Column(JSON, nullable=False) # JSON metadata of column names, byte maps, types
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    records = relationship("SurveyRecord", back_populates="survey", cascade="all, delete-orphan")
    rules = relationship("ValidationRule", back_populates="survey", cascade="all, delete-orphan")
    models = relationship("MLModel", back_populates="survey", cascade="all, delete-orphan")
    fingerprints = relationship("EnumeratorFingerprint", back_populates="survey", cascade="all, delete-orphan")


class SurveyRecord(Base):
    __tablename__ = "survey_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False, index=True)
    record_id = Column(String, nullable=False, index=True) # Domain record identifier
    survey_round = Column(String, nullable=False, index=True) # e.g. 2023-24 or 2024-25
    state_code = Column(String, nullable=False, index=True) # e.g. 09 (UP), 27 (MH)
    district_code = Column(String, nullable=True, index=True)
    sector = Column(String, nullable=True, index=True) # Rural = 1, Urban = 2
    fsu_id = Column(String, nullable=True, index=True) # First Stage Unit / Enumerator proxy
    raw_payload = Column(JSON, nullable=False) # Full record dictionary (survey-agnostic JSONB)
    ingested_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    survey = relationship("Survey", back_populates="records")
    flags = relationship("AnomalyFlag", back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_records_survey_round_state", "survey_id", "survey_round", "state_code"),
    )


class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False, index=True)
    rule_code = Column(String, nullable=False, index=True) # e.g. RULE_AGE_EDU
    name = Column(String, nullable=False)
    category = Column(String, nullable=False) # referential_integrity, range, logical_consistency
    severity = Column(String, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    rule_json = Column(JSON, nullable=False) # Structured rule logic: target_field, operator, value/field2
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey", back_populates="rules")


class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"

    id = Column(String, primary_key=True, default=generate_uuid)
    record_id = Column(String, ForeignKey("survey_records.id"), nullable=False, index=True)
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False, index=True)
    detector_type = Column(String, nullable=False, index=True) # RULE_ENGINE, Z_SCORE, IQR, ISOLATION_FOREST, LOF, ENSEMBLE
    severity = Column(String, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    score = Column(Float, nullable=False)
    evidence = Column(JSON, nullable=False) # Bullets, cohort details, percentiles, field contributions
    status = Column(String, default="PENDING", index=True) # PENDING, CONFIRMED, DISMISSED
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    record = relationship("SurveyRecord", back_populates="flags")
    feedback = relationship("SupervisorFeedback", back_populates="flag", uselist=False, cascade="all, delete-orphan")


class EnumeratorFingerprint(Base):
    __tablename__ = "enumerator_fingerprints"

    id = Column(String, primary_key=True, default=generate_uuid)
    enumerator_id = Column(String, nullable=False, index=True)
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False, index=True)
    total_records = Column(Integer, default=0)
    missing_rate = Column(Float, default=0.0)
    digit_preference_score = Column(Float, default=0.0)
    historical_anomaly_rate = Column(Float, default=0.0)
    composite_risk_score = Column(Float, default=0.0)
    metrics_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    survey = relationship("Survey", back_populates="fingerprints")


class SupervisorFeedback(Base):
    __tablename__ = "supervisor_feedback"

    id = Column(String, primary_key=True, default=generate_uuid)
    flag_id = Column(String, ForeignKey("anomaly_flags.id"), nullable=False, index=True)
    supervisor_id = Column(String, nullable=False)
    decision = Column(String, nullable=False) # CONFIRMED, DISMISSED
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    flag = relationship("AnomalyFlag", back_populates="feedback")


class MLModel(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True, default=generate_uuid)
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False, index=True)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    algorithm = Column(String, nullable=False) # ISOLATION_FOREST, LOF, ENSEMBLE
    hyperparameters = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=True) # precision, recall, f1
    artifact_path = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey", back_populates="models")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    actor_id = Column(String, nullable=False)
    actor_role = Column(String, nullable=False) # ADMIN, SUPERVISOR, VIEWER
    action = Column(String, nullable=False) # RULE_UPDATE, MODEL_TRAIN, DECISION_SUBMIT
    entity_type = Column(String, nullable=False) # validation_rules, models, anomaly_flags
    entity_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
