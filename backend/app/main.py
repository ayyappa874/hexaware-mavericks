import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import health, surveys, records, rules, enumerators, temporal, models_lab, feedback, counterfactual, replay, auth, reports, clusters, audit_chain, canary, offline_p2p
from app.db.session import engine, Base

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Survey Sentinel - Production-Grade MoSPI Government Survey Data Validation Platform"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Auth"])
app.include_router(reports.router, prefix=settings.API_V1_STR, tags=["Reports"])
app.include_router(clusters.router, prefix=settings.API_V1_STR, tags=["Anomaly Clusters"])
app.include_router(audit_chain.router, prefix=settings.API_V1_STR, tags=["Audit Chain"])
app.include_router(canary.router, prefix=settings.API_V1_STR, tags=["Canary Self-Audit"])
app.include_router(offline_p2p.router, prefix=settings.API_V1_STR, tags=["Offline P2P Hotspot"])
app.include_router(surveys.router, prefix=settings.API_V1_STR, tags=["Surveys"])
app.include_router(records.router, prefix=settings.API_V1_STR, tags=["Records"])
app.include_router(rules.router, prefix=settings.API_V1_STR, tags=["Rules"])
app.include_router(enumerators.router, prefix=settings.API_V1_STR, tags=["Enumerators"])
app.include_router(temporal.router, prefix=settings.API_V1_STR, tags=["Temporal Drift"])
app.include_router(models_lab.router, prefix=settings.API_V1_STR, tags=["Model Lab"])
app.include_router(feedback.router, prefix=settings.API_V1_STR, tags=["Supervisor Feedback"])
app.include_router(counterfactual.router, prefix=settings.API_V1_STR, tags=["Counterfactual Explanations"])
app.include_router(replay.router, prefix=settings.API_V1_STR, tags=["Stream Replay Demo"])

@app.on_event("startup")
def startup_event():
    logger.info("Initializing database tables on startup...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"{settings.PROJECT_NAME} backend started successfully.")

@app.get("/")
def root():
    return {
        "title": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
        "status": "active"
    }
