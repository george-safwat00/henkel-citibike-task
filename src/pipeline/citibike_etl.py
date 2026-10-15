"""
Citi Bike ETL Pipeline.
"""
from src.logger import get_logger
from src.extract.downloader import DataDownloader
from src.extract.extractor import DataExtractor
from src.load.loader import RawDataLoader
from src.transform.cleaning import DataTransformer

logger = get_logger(__name__)

def citibike_pipeline():
    # Phase 1: Extract & Load (Bronze)
    logger.info("--- Phase 1: Download & Extract ---")
    downloader = DataDownloader()
    zip_path = downloader.download()
    
    extractor = DataExtractor(zip_path=zip_path)
    extractor.extract()

    logger.info("--- Phase 2: Load to Bronze (Raw Parquet) ---")
    loader = RawDataLoader()
    loader.load()
    
    # Phase 3: Transform (Silver)
    logger.info("--- Phase 3: Transform to Silver (Clean Star Schema) ---")
    transformer = DataTransformer()
    transformer.transform()
    
    logger.info("--- ETL Pipeline Complete ---")