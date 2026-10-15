"""
Main entry point to run the download and extraction pipeline.
"""
from src.logger import get_logger
from src.pipeline.citibike_etl import citibike_pipeline

logger = get_logger(__name__)

def main():
    citibike_pipeline()

if __name__ == "__main__":
    main()