"""
Module for loading raw scattered CSV files into a single consolidated 'Bronze' Parquet file.
"""
import polars as pl
from pathlib import Path

from src.config import RAW_EXTRACTED_DIR, PROCESSED_DIR
from src.logger import get_logger

logger = get_logger(__name__)

# Map the messy original CSV column names to clean snake_case
COLUMN_MAPPING = {
    "tripduration": "trip_duration_seconds",
    "starttime": "start_time",
    "stoptime": "stop_time",
    "start station id": "start_station_id",
    "start station name": "start_station_name",
    "start station latitude": "start_station_lat",
    "start station longitude": "start_station_lon",
    "end station id": "end_station_id",
    "end station name": "end_station_name",
    "end station latitude": "end_station_lat",
    "end station longitude": "end_station_lon",
    "bikeid": "bike_id",
    "usertype": "user_type",
    "birth year": "birth_year",
    "gender": "gender_id"
}

class RawDataLoader:
    """
    Ingests raw monthly CSVs into a single, uncleaned 'Bronze' Parquet file.
    """

    def __init__(self, source_dir: Path = RAW_EXTRACTED_DIR, output_dir: Path = PROCESSED_DIR):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_file = output_dir / "trips_raw_bronze.parquet"

    def load(self) -> Path:
        """
        Scans all CSVs, renames columns to snake_case, casts to safe basic types, 
        and writes to a single raw Parquet file.
        """
        if self.output_file.exists():
            logger.info(f"Raw Bronze file already exists: {self.output_file}. Skipping load.")
            return self.output_file

        csv_pattern = str(self.source_dir / "**" / "*.csv")
        logger.info(f"Loading raw CSVs from: {csv_pattern}")

        try:
            # Scan CSVs. We disable try_parse_dates to preserve the messy US date format as strings.
            lazy_df = pl.scan_csv(
                csv_pattern,
                try_parse_dates=False, 
                ignore_errors=True,
                include_file_paths="source_file"
            )

            # Rename columns to clean snake_case
            lazy_df = lazy_df.rename(COLUMN_MAPPING)

            # Cast to safe, basic types for the Bronze layer
            # Note: start_time and stop_time remain Utf8 (String) for the Transformer to handle.
            cast_exprs = [
                pl.col("trip_duration_seconds").cast(pl.Int64),
                pl.col("start_station_id").cast(pl.Int64),
                pl.col("end_station_id").cast(pl.Int64),
                pl.col("bike_id").cast(pl.Int64),
                pl.col("start_station_lat").cast(pl.Float64),
                pl.col("start_station_lon").cast(pl.Float64),
                pl.col("end_station_lat").cast(pl.Float64),
                pl.col("end_station_lon").cast(pl.Float64),
                pl.col("birth_year").cast(pl.Int64),
                pl.col("gender_id").cast(pl.Int64),
                pl.col("user_type").cast(pl.Utf8),
                pl.col("start_time").cast(pl.Utf8),
                pl.col("stop_time").cast(pl.Utf8),
            ]
            
            lazy_df = lazy_df.with_columns(cast_exprs)

            self.output_dir.mkdir(parents=True, exist_ok=True)
            lazy_df.sink_parquet(self.output_file)

            self._validate_load()
            logger.info(f"Successfully loaded raw data to: {self.output_file}")
            return self.output_file

        except Exception as e:
            logger.error(f"Failed to load raw data: {e}")
            raise

    def _validate_load(self) -> None:
        """Basic validation to ensure the file was created and has the expected columns."""
        if not self.output_file.exists():
            raise FileNotFoundError(f"Load failed: {self.output_file} was not created.")
        
        schema = pl.read_parquet_schema(self.output_file)
        expected_cols = set(COLUMN_MAPPING.values()) | {"source_file"}
        if not expected_cols.issubset(set(schema.keys())):
            raise ValueError(f"Load validation failed. Missing columns in schema: {expected_cols - set(schema.keys())}")