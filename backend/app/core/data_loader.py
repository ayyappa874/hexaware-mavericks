import os
import json
import logging
import pandas as pd
import polars as pl
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models.schema import Survey, SurveyRecord

logger = logging.getLogger(__name__)

class PLFSDataLoader:
    def __init__(self, layout_filepath: str = "data/plfs_layout.json"):
        self.layout_filepath = layout_filepath
        self.schema_map = self.parse_layout_file(layout_filepath)

    def parse_layout_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parses a PLFS data-layout file (column name, byte start/end, description, data_type)
        into a structured python schema map.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Data layout file not found at: {filepath}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            layout_data = json.load(f)

        schema_map = {
            "survey_code": layout_data.get("survey_code", "PLFS_2024"),
            "survey_name": layout_data.get("survey_name", "Periodic Labour Force Survey"),
            "description": layout_data.get("description", ""),
            "columns": layout_data.get("columns", [])
        }
        logger.info(f"Successfully parsed layout file '{filepath}'. Found {len(schema_map['columns'])} column specifications.")
        return schema_map

    def parse_fixed_width_txt(self, txt_filepath: str) -> pl.DataFrame:
        """
        Converts raw fixed-width .txt files (e.g. CHHV1.txt) into a Polars DataFrame using byte-position mapping.
        """
        if not os.path.exists(txt_filepath):
            raise FileNotFoundError(f"Fixed-width file not found: {txt_filepath}")

        cols = self.schema_map["columns"]
        records = []

        with open(txt_filepath, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                if not line.strip():
                    continue
                row_dict = {}
                for col in cols:
                    start = col["start_byte"] - 1 # 1-indexed to 0-indexed
                    end = col["end_byte"]
                    raw_val = line[start:end].strip()

                    # Convert types based on schema
                    dtype = col.get("data_type", "string")
                    if dtype == "integer":
                        try:
                            row_dict[col["name"]] = int(raw_val) if raw_val else 0
                        except ValueError:
                            row_dict[col["name"]] = 0
                    elif dtype == "float":
                        try:
                            row_dict[col["name"]] = float(raw_val) if raw_val else 0.0
                        except ValueError:
                            row_dict[col["name"]] = 0.0
                    else:
                        row_dict[col["name"]] = str(raw_val)

                records.append(row_dict)

        df = pl.DataFrame(records)
        logger.info(f"Parsed {len(df)} records from fixed-width file: {txt_filepath}")
        return df

    def parse_headered_csv(self, csv_filepath: str) -> pl.DataFrame:
        """
        Fallback parser: Loads pre-converted CSV microdata with headers into Polars DataFrame.
        """
        if not os.path.exists(csv_filepath):
            raise FileNotFoundError(f"CSV microdata file not found: {csv_filepath}")
        
        df = pl.read_csv(csv_filepath)
        logger.info(f"Parsed {len(df)} records from headered CSV file: {csv_filepath}")
        return df

    def convert_to_parquet(self, df: pl.DataFrame, output_parquet_path: str) -> str:
        """
        Saves clean microdata DataFrame as optimized Parquet format.
        """
        os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
        df.write_parquet(output_parquet_path)
        logger.info(f"Exported DataFrame to Parquet at: {output_parquet_path}")
        return output_parquet_path

    def load_plfs_data(self, data_path: str = "data/plfs_microdata.csv") -> pl.DataFrame:
        """
        Main loader function: checks if fixed-width .txt exists, otherwise falls back to pre-converted CSV.
        """
        if data_path.endswith(".txt") or os.path.exists("data/CHHV1.txt"):
            txt_file = data_path if data_path.endswith(".txt") else "data/CHHV1.txt"
            logger.info(f"Loading fixed-width raw PLFS file from {txt_file}")
            df = self.parse_fixed_width_txt(txt_file)
        elif os.path.exists(data_path):
            logger.info(f"Loading pre-converted CSV PLFS microdata from {data_path}")
            df = self.parse_headered_csv(data_path)
        else:
            raise FileNotFoundError(f"Neither fixed-width nor CSV microdata found at {data_path}")
        
        return df

    def split_rounds(self, df: pl.DataFrame) -> Tuple[pl.DataFrame, pl.DataFrame]:
        """
        Splits dataset by survey round:
        - Baseline: earlier survey rounds (e.g. 2023-24)
        - Incoming Demo Stream: most recent round (e.g. 2024-25)
        """
        unique_rounds = sorted(df["Survey_Round"].unique().to_list())
        if len(unique_rounds) <= 1:
            logger.warning("Only 1 survey round present in dataset. Baseline and incoming streams will share the round.")
            return df, df

        most_recent_round = unique_rounds[-1]
        baseline_rounds = unique_rounds[:-1]

        df_baseline = df.filter(pl.col("Survey_Round").is_in(baseline_rounds))
        df_incoming = df.filter(pl.col("Survey_Round") == most_recent_round)

        logger.info(f"Split data into baseline ({len(df_baseline)} rows, rounds {baseline_rounds}) and incoming demo stream ({len(df_incoming)} rows, round '{most_recent_round}').")
        return df_baseline, df_incoming

    def load_to_database(self, db: Session, df: pl.DataFrame, survey_id: str) -> int:
        """
        Loads cleaned PLFS records into PostgreSQL 'survey_records',
        tagging each row with round, state_code, district_code, sector, and fsu_id.
        """
        # Convert polars DataFrame to dict rows
        rows = df.to_dicts()
        inserted_count = 0

        db_records = []
        for idx, row in enumerate(rows):
            # Extract standard tags
            s_round = str(row.get("Survey_Round", "2023-24"))
            s_state = str(row.get("State", "00")).zfill(2)
            s_dist = str(row.get("District", "00")).zfill(3)
            s_sector = str(row.get("Sector", "1"))
            s_fsu = str(row.get("FSU", "FSU000"))
            rec_id = f"REC_{s_round}_{s_state}_{s_fsu}_{row.get('Hh_No', 0)}_{row.get('Person_No', 0)}_{idx}"

            db_record = SurveyRecord(
                survey_id=survey_id,
                record_id=rec_id,
                survey_round=s_round,
                state_code=s_state,
                district_code=s_dist,
                sector=s_sector,
                fsu_id=s_fsu,
                raw_payload=row # Entire record stored in JSONB
            )
            db_records.append(db_record)

            if len(db_records) >= 200:
                db.bulk_save_objects(db_records)
                db.commit()
                inserted_count += len(db_records)
                db_records = []

        if db_records:
            db.bulk_save_objects(db_records)
            db.commit()
            inserted_count += len(db_records)

        logger.info(f"Successfully loaded {inserted_count} PLFS microdata records into Postgres 'survey_records'.")
        return inserted_count
