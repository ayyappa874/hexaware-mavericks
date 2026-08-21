from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.schema import Survey, MLModel, AuditLog
from app.engines.model_lab_engine import ModelLabEngine

router = APIRouter()

class TrainModelInput(BaseModel):
    survey_code: str = "PLFS_2024"
    model_name: str = "PLFS_IsolationForest_v1"
    algorithm: str = "ISOLATION_FOREST" # ISOLATION_FOREST, LOF, STATISTICAL_ENSEMBLE
    hyperparameters: Optional[Dict[str, Any]] = {"n_estimators": 100, "contamination": 0.05}
    features: Optional[List[str]] = None
    train_round: str = "2023-24"
    test_round: str = "2024-25"

@router.get("/models")
def list_models(survey_code: str = "PLFS_2024", db: Session = Depends(get_db)):
    """
    List all trained model versions and comparison metrics table.
    """
    survey = db.query(Survey).filter(Survey.code == survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{survey_code}' not found.")

    models = db.query(MLModel).filter(MLModel.survey_id == survey.id).order_by(MLModel.trained_at.desc()).all()

    return [
        {
            "id": m.id,
            "survey_id": m.survey_id,
            "model_name": m.model_name,
            "version": m.version,
            "algorithm": m.algorithm,
            "hyperparameters": m.hyperparameters,
            "metrics": m.metrics,
            "is_active": m.is_active,
            "trained_at": m.trained_at
        }
        for m in models
    ]

@router.post("/models/train")
def train_model(data: TrainModelInput, db: Session = Depends(get_db)):
    """
    Train a custom anomaly detection model on historical survey round data (e.g. 2023-24)
    and evaluate performance against held-out round data (e.g. 2024-25).
    """
    survey = db.query(Survey).filter(Survey.code == data.survey_code).first()
    if not survey:
        raise HTTPException(status_code=404, detail=f"Survey '{data.survey_code}' not found.")

    try:
        model_obj = ModelLabEngine.train_and_evaluate(
            db=db,
            survey_id=survey.id,
            model_name=data.model_name,
            algorithm=data.algorithm,
            hyperparameters=data.hyperparameters,
            features=data.features,
            train_round=data.train_round,
            test_round=data.test_round
        )

        return {
            "status": "success",
            "message": f"Model '{model_obj.model_name}' ({model_obj.version}) trained and evaluated successfully.",
            "model": {
                "id": model_obj.id,
                "model_name": model_obj.model_name,
                "version": model_obj.version,
                "algorithm": model_obj.algorithm,
                "hyperparameters": model_obj.hyperparameters,
                "metrics": model_obj.metrics,
                "is_active": model_obj.is_active,
                "trained_at": model_obj.trained_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/models/{model_id}/promote")
def promote_champion_model(model_id: str, db: Session = Depends(get_db)):
    """
    Promotes specified model version to active "CHAMPION" model for the survey.
    Deactivates any previously active champion models.
    """
    target_model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not target_model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")

    # Deactivate all other models for this survey
    db.query(MLModel).filter(MLModel.survey_id == target_model.survey_id).update({"is_active": False})

    # Activate target champion model
    target_model.is_active = True

    # Audit trail entry
    audit = AuditLog(
        actor_id="SUPERVISOR_USER",
        actor_role="SUPERVISOR",
        action="PROMOTE_CHAMPION_MODEL",
        entity_type="models",
        entity_id=target_model.id,
        details={
            "promoted_model_name": target_model.model_name,
            "promoted_version": target_model.version,
            "algorithm": target_model.algorithm,
            "metrics": target_model.metrics
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(target_model)

    return {
        "status": "success",
        "message": f"Model '{target_model.model_name}' ({target_model.version}) successfully promoted to active CHAMPION model.",
        "champion_model": {
            "id": target_model.id,
            "model_name": target_model.model_name,
            "version": target_model.version,
            "algorithm": target_model.algorithm,
            "metrics": target_model.metrics,
            "is_active": target_model.is_active
        }
    }
