"""
Diagnostic script to analyze why rows are being dropped during transformation.
Run this from the root directory: python scripts/diagnose_dropped_rows.py
"""
import polars as pl
from pathlib import Path
from src.utils.haversine import haversine_distance_km_expr

def main():
    bronze_path = Path("data/processed/trips_raw_bronze.parquet")
    if not bronze_path.exists():
        print(f"Error: {bronze_path} not found. Run the pipeline first.")
        return

    print(f"Loading {bronze_path}...")
    df = pl.read_parquet(bronze_path)
    total_rows = len(df)
    print(f"Total rows in Bronze: {total_rows:,}\n")

    # 1. Parse Dates (Try ISO first, then US format if needed)
    # We use strict=False so bad dates become null instead of crashing
    df = df.with_columns([
        pl.col("start_time").str.to_datetime(format="%Y-%m-%d %H:%M:%S%.f", strict=False).alias("start_dt_iso"),
        pl.col("start_time").str.to_datetime(format="%m/%d/%Y %I:%M:%S %p", strict=False).alias("start_dt_us"),
        pl.col("stop_time").str.to_datetime(format="%Y-%m-%d %H:%M:%S%.f", strict=False).alias("stop_dt_iso"),
        pl.col("stop_time").str.to_datetime(format="%m/%d/%Y %I:%M:%S %p", strict=False).alias("stop_dt_us"),
    ])

    # Coalesce: Use ISO if parsed, else use US, else null
    df = df.with_columns([
        pl.coalesce("start_dt_iso", "start_dt_us").alias("start_dt"),
        pl.coalesce("stop_dt_iso", "stop_dt_us").alias("stop_dt"),
    ])

    # 2. Calculate Speed
    df = df.with_columns([
        haversine_distance_km_expr("start_station_lat", "start_station_lon", "end_station_lat", "end_station_lon").alias("distance_km"),
        ((haversine_distance_km_expr("start_station_lat", "start_station_lon", "end_station_lat", "end_station_lon") / pl.col("trip_duration_seconds")) * 3600).round(2).alias("speed_kmh")
    ])

    # 3. Define Failure Masks (True = Row is Invalid)
    
    # Rule 1: Duration
    mask_duration = (pl.col("trip_duration_seconds") <= 0) | (pl.col("trip_duration_seconds") > 86400)
    
    # Rule 2: Time Logic (Includes unparseable dates which result in nulls)
    mask_time = pl.col("start_dt").is_null() | pl.col("stop_dt").is_null() | (pl.col("start_dt") >= pl.col("stop_dt"))
    
    # Rule 3: Speed (Ignore nulls, as they are handled by Lat/Lon rule)
    mask_speed = (pl.col("speed_kmh").is_not_null()) & ((pl.col("speed_kmh") > 40.0) | (pl.col("speed_kmh") < 0))
    
    # Rule 4: Geography (NYC Bounds)
    mask_lat = (pl.col("start_station_lat").is_not_null()) & (~pl.col("start_station_lat").is_between(40.4, 41.0))
    mask_lon = (pl.col("start_station_lon").is_not_null()) & (~pl.col("start_station_lon").is_between(-74.3, -73.7))

    # 4. Calculate Counts
    count_duration = df.filter(mask_duration).height
    count_time = df.filter(mask_time).height
    count_speed = df.filter(mask_speed).height
    count_lat = df.filter(mask_lat).height
    count_lon = df.filter(mask_lon).height

    # Note: A row can fail multiple rules, so these numbers won't sum exactly to 6,132.
    print("--- DROPPED ROW ANALYSIS ---")
    print(f"Failed Duration Rule (<=0s or >24h): {count_duration:,}")
    print(f"Failed Time Rule (Null dates or Start >= Stop): {count_time:,}")
    print(f"Failed Speed Rule (>40km/h): {count_speed:,}")
    print(f"Failed Lat Rule (Outside NYC): {count_lat:,}")
    print(f"Failed Lon Rule (Outside NYC): {count_lon:,}")
    print("----------------------------\n")

    # 5. Export Sample of Dropped Rows
    # Combine all masks to find the actual dropped rows
    mask_dropped = mask_duration | mask_time | mask_speed | mask_lat | mask_lon
    dropped_df = df.filter(mask_dropped)
    
    export_path = Path("data/processed/dropped_rows_sample.csv")
    dropped_df.head(100).write_csv(export_path)
    print(f"Exported first 100 dropped rows to: {export_path}")
    print("Open this file in Excel to inspect the raw data.")

if __name__ == "__main__":
    main()