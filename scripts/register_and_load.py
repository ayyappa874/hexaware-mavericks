import sys
import os
import logging

# Ensure app modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal, engine, Base
from app.models.schema import Survey, SurveyRecord
from app.core.schema_registry import register_plfs_survey
from app.core.data_loader import PLFSDataLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Step 1: Register PLFS Survey Schema & Rules
        logger.info("Registering PLFS survey schema...")
        survey = register_plfs_survey(db, layout_path="data/plfs_layout.json")

        # Step 2: Clear old records for clean run if requested
        existing_count = db.query(SurveyRecord).filter(SurveyRecord.survey_id == survey.id).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing records in survey_records. Clearing for fresh load...")
            db.query(SurveyRecord).filter(SurveyRecord.survey_id == survey.id).delete()
            db.commit()

        # Step 3: Parse and load microdata
        loader = PLFSDataLoader(layout_filepath="data/plfs_layout.json")
        df = loader.load_plfs_data("data/plfs_microdata.csv")

        # Convert and save Parquet cache as well
        loader.convert_to_parquet(df, "data/plfs_microdata.parquet")

        # Step 4: Bulk insert into Postgres survey_records
        loaded_count = loader.load_to_database(db, df, survey.id)

        # Step 5: Summary log
        rounds_summary = df.group_by("Survey_Round").count().to_dicts()
        states_count = len(df["State"].unique())
        logger.info("═══════════════════════════════════════════════════════════════")
        logger.info("               SURVEY SENTINEL INGESTION SUCCESS               ")
        logger.info("═══════════════════════════════════════════════════════════════")
        logger.info(f"Survey Name: {survey.name} (Code: {survey.code})")
        logger.info(f"Total Loaded Records: {loaded_count}")
        logger.info(f"States Represented: {states_count}")
        logger.info(f"Round Breakdown: {rounds_summary}")
        logger.info("═══════════════════════════════════════════════════════════════")

    except Exception as e:
        logger.error(f"Error during registration and loading: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
