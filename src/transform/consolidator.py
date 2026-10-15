"""
Module for consolidating scattered raw CSV files into a single optimized Parquet file.
"""
import polars as pl
from pathlib import Path

from src.config import RAW_EXTRACTED_DIR, PROCESSED_DIR
from src.logger import get_logger

logger = get_logger(__name__)


class DataConsolidator:
    """
    Consolidates multiple monthly CSV files into a single Parquet file.
    Uses Polars lazy evaluation to ensure memory efficiency on large datasets.
    """

    def __init__(self, source_dir: Path = RAW_EXTRACTED_DIR, output_dir: Path = PROCESSED_DIR):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_file = output_dir / "trips_consolidated.parquet"

    def consolidate(self) -> Path:
        """
        Scans all CSVs in the source directory tree, combines them, 
        and writes to a single Parquet file.
        
        Returns:
            Path: The path to the consolidated Parquet file.
        """
        if self.output_file.exists():
            logger.info(f"Consolidated file already exists: {self.output_file}")
            return self.output_file

        # Glob pattern to match all CSVs in all month subdirectories
        # e.g., data/raw/extracted/2019/1_January/*.csv
        csv_pattern = str(self.source_dir / "**" / "*.csv")
        logger.info(f"Scanning for CSV files matching: {csv_pattern}")

        try:
            # scan_csv is lazy: it builds a query plan without loading data into memory
            # include_file_paths adds a column showing which file the row came from (great for debugging)
            # try_parse_dates automatically infers and parses datetime columns
            lazy_df = pl.scan_csv(
                csv_pattern,
                try_parse_dates=True,
                ignore_errors=True,  # Skip rows with unparseable data rather than crashing
                include_file_paths="source_file"
            )

            logger.info("Executing consolidation pipeline (streaming to disk)...")
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # sink_parquet writes the lazy dataframe directly to disk in chunks
            # This prevents Out-Of-Memory (OOM) errors on 16GB RAM machines
            lazy_df.sink_parquet(self.output_file)

            self._validate_consolidation()
            logger.info(f"Successfully consolidated data to: {self.output_file}")
            return self.output_file

        except Exception as e:
            logger.error(f"Failed to consolidate data: {e}")
            raise

    def _validate_consolidation(self) -> None:
        """Basic validation to ensure the Parquet file was created and is not empty."""
        if not self.output_file.exists():
            raise FileNotFoundError(f"Consolidation failed: {self.output_file} was not created.")
        
        # Quick peek at the row count without loading the whole file
        # (Polars can read just the metadata of a parquet file very quickly)
        # We'll do a simple check by reading the schema
        schema = pl.read_parquet_schema(self.output_file)
        if not schema:
            raise ValueError("Consolidation failed: Parquet file has no schema/is empty.")
        
        logger.info(f"Validation passed. Parquet schema contains {len(schema)} columns.")