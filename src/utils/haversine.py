"""
Utility functions for geographic calculations.
"""
import polars as pl

def haversine_distance_km_expr(
    lat1_col: str, lon1_col: str, lat2_col: str, lon2_col: str
) -> pl.Expr:
    """
    Returns a Polars expression to calculate the Haversine distance in kilometers
    between two sets of latitude/longitude columns.
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = pl.col(lat1_col).radians()
    lon1_rad = pl.col(lon1_col).radians()
    lat2_rad = pl.col(lat2_col).radians()
    lon2_rad = pl.col(lon2_col).radians()

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = (dlat / 2).sin().pow(2) + lat1_rad.cos() * lat2_rad.cos() * (dlon / 2).sin().pow(2)
    c = 2 * a.sqrt().arcsin()
    
    return (R * c).round(4).alias("distance_km")