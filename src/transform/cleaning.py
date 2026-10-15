"""
Module for transforming the raw Bronze Parquet into a clean, analysis-ready Silver Star Schema.
"""
import polars as pl
from pathlib import Path

from src.config import PROCESSED_DIR
from src.logger import get_logger
from src.utils.haversine import haversine_distance_km_expr

logger = get_logger(__name__)


class DataTransformer:
    """
    Transforms raw Bronze trip data into a clean, analysis-ready Silver Star Schema.
    """

    def __init__(self, input_file: Path = PROCESSED_DIR / "trips_raw_bronze.parquet"):
        self.input_file = input_file
        self.output_dir = PROCESSED_DIR

    def transform(self) -> dict[str, Path]:
        """
        Executes the full transformation pipeline.
        """
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}. Run the Loader first.")

        logger.info("Loading Bronze data for transformation...")
        df = pl.read_parquet(self.input_file)
        initial_count = len(df)
        logger.info(f"Loaded {initial_count:,} raw rows.")

        # 1. Parse Dates
        logger.info("Parsing datetime columns...")
        df = df.with_columns([
            pl.col("start_time").str.to_datetime(format="%Y-%m-%d %H:%M:%S%.f", strict=False),
            pl.col("stop_time").str.to_datetime(format="%Y-%m-%d %H:%M:%S%.f", strict=False)
        ])

        # 2. Feature Engineering: Demographics & User Type IDs
        logger.info("Mapping demographics and calculating age...")
        
        # Map User Type string to ID for the Fact table
        user_type_map = {"Customer": 1, "Subscriber": 2}
        
        df = df.with_columns([
            # Keep gender_id as is (0=Unknown, 1=Male, 2=Female)
            (2019 - pl.col("birth_year")).alias("age"),
            pl.col("user_type").replace(user_type_map).alias("user_type_id")
        ])
        
        # Cap age: if age < 12 or > 90, set to null
        df = df.with_columns(
            pl.when(pl.col("age").is_between(12, 90))
              .then(pl.col("age"))
              .otherwise(None).alias("age")
        )

        # 3. Feature Engineering: Distance & Speed (Haversine)
        logger.info("Calculating Haversine distance and average speed...")
        df = df.with_columns([
            haversine_distance_km_expr("start_station_lat", "start_station_lon", "end_station_lat", "end_station_lon"),
            ((haversine_distance_km_expr("start_station_lat", "start_station_lon", "end_station_lat", "end_station_lon") / pl.col("trip_duration_seconds")) * 3600)
            .round(2).alias("speed_kmh")
        ])

        # 4. Data Quality Filtering
        logger.info("Applying data quality filters...")
        initial_filtered_count = len(df)
        
        df = df.filter([
            (pl.col("trip_duration_seconds") > 0) & (pl.col("trip_duration_seconds") <= 86400),
            pl.col("start_time") < pl.col("stop_time"),
            (pl.col("speed_kmh").is_null() | ((pl.col("speed_kmh") >= 0) & (pl.col("speed_kmh") <= 40.0))),
            (pl.col("start_station_lat").is_null() | pl.col("start_station_lat").is_between(40.4, 41.0)) &
            (pl.col("start_station_lon").is_null() | pl.col("start_station_lon").is_between(-74.3, -73.7))
        ])

        # Filter out rows with missing station data (The 180 nulls from profiling)
        initial_station_count = len(df)
        df = df.filter(
            pl.col("start_station_id").is_not_null() &
            pl.col("start_station_name").is_not_null() &
            pl.col("start_station_lat").is_not_null() &
            pl.col("start_station_lon").is_not_null()
        )
        dropped_station_count = initial_station_count - len(df)
        if dropped_station_count > 0:
            logger.info(f"Filtered out {dropped_station_count} trips with missing station data.")

        final_count = len(df)
        dropped_count = initial_filtered_count - final_count
        logger.info(f"Filtered out {dropped_count:,} invalid rows ({(dropped_count/initial_filtered_count)*100:.2f}% of data).")

        # 5. Generate Trip ID
        df = df.with_row_index("trip_id", offset=1)

        # 6. Validation Check
        self._validate_clean_data(df)

        # 7. Save Outputs (Star Schema preparation)
        logger.info("Saving transformed Silver data to Parquet...")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # --- FACT TABLE ---
        fact_cols_to_drop = [
            "user_type", 
            "start_station_name", 
            "end_station_name", 
            "source_file",
            "start_station_lat", 
            "start_station_lon", 
            "end_station_lat", 
            "end_station_lon"
        ]

        cols_to_drop = [c for c in fact_cols_to_drop if c in df.columns]
        df_fact = df.drop(cols_to_drop)
        
        fact_path = self.output_dir / "fact_trips_clean.parquet"
        df_fact.write_parquet(fact_path, compression="zstd")
        logger.info(f"Saved fact table to: {fact_path}")

        # --- DIMENSION TABLES ---
        
        # 1. Station Dimension (Handle duplicate station_ids by keeping most frequent coords)
        dim_station_path = self.output_dir / "dim_station.parquet"
        
        # Group by station_id, name, lat, lon and count occurrences
        station_counts = df.group_by([
            "start_station_id",
            "start_station_name", 
            "start_station_lat",
            "start_station_lon"
        ]).agg(
            pl.len().alias("occurrence_count")
        )
        
        # For each station_id, keep the row with the highest occurrence count
        dim_station = (
            station_counts.sort(["start_station_id", "occurrence_count"], descending=[False, True])
            .group_by("start_station_id")
            .first()  # Takes the first row (which has highest count due to sort)
            .select([
                pl.col("start_station_id").alias("station_id"),
                pl.col("start_station_name").alias("station_name"),
                pl.col("start_station_lat").alias("latitude"),
                pl.col("start_station_lon").alias("longitude")
            ])
        )
        
        dim_station.write_parquet(dim_station_path, compression="zstd")
        logger.info(f"Saved station dimension ({len(dim_station)} unique stations) to: {dim_station_path}")

        # 2. Gender Dimension
        dim_gender_path = self.output_dir / "dim_gender.parquet"
        dim_gender_df = pl.DataFrame({
            "gender_id": [0, 1, 2],
            "gender_name": ["Unknown", "Male", "Female"]
        })
        dim_gender_df.write_parquet(dim_gender_path, compression="zstd")
        logger.info(f"Saved gender dimension to: {dim_gender_path}")

        # 3. User Type Dimension
        dim_user_type_path = self.output_dir / "dim_user_type.parquet"
        dim_user_type_df = pl.DataFrame({
            "user_type_id": [1, 2],
            "user_type_name": ["Customer", "Subscriber"]
        })
        dim_user_type_df.write_parquet(dim_user_type_path, compression="zstd")
        logger.info(f"Saved user type dimension to: {dim_user_type_path}")

        return {
            "fact_trips": fact_path,
            "dim_station": dim_station_path,
            "dim_gender": dim_gender_path,
            "dim_user_type": dim_user_type_path
        }

    def _validate_clean_data(self, df: pl.DataFrame) -> None:
        """Post-transformation validation to ensure data integrity."""
        logger.info("Running post-transformation validations...")
        
        # Check critical columns (updated to use IDs instead of strings)
        critical_cols = ["trip_duration_seconds", "start_time", "user_type_id", "gender_id"]
        for col in critical_cols:
            null_count = df[col].null_count()
            if null_count > 0:
                logger.warning(f"Validation Warning: {null_count} nulls found in critical column '{col}'.")

        # Check speed bounds
        valid_speeds = df.filter(pl.col("speed_kmh").is_not_null())
        if len(valid_speeds) > 0:
            max_speed = valid_speeds["speed_kmh"].max()
            if max_speed is not None and float(max_speed) > 40.0:
                raise ValueError(f"Validation Failed: Max speed {max_speed} km/h exceeds safe threshold.")

        logger.info("All post-transformation validations passed successfully.")