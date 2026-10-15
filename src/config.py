"""
Project configuration and path definitions.
"""
from pathlib import Path

# Project root directory (assuming config.py is in src/)
ROOT_DIR = Path(__file__).parent.parent

# Data paths
RAW_ZIPS_DIR = ROOT_DIR / "data" / "raw" / "zips" / "2019"
RAW_EXTRACTED_DIR = ROOT_DIR / "data" / "raw" / "extracted" / "2019"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" 

# Download settings
S3_BASE_URL = "https://s3.amazonaws.com/tripdata/"
MAIN_ZIP_FILENAME = "2019-citibike-tripdata.zip"

# Expected folder structure inside the zip
EXPECTED_MONTHS = [
    "1_January", "2_February", "3_March", "4_April", "5_May", "6_June",
    "7_July", "8_August", "9_September", "10_October", "11_November", "12_December"
]   