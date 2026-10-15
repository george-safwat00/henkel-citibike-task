"""
Module for downloading raw data from remote sources.
"""
import requests
from pathlib import Path
from tqdm import tqdm

from src.config import RAW_ZIPS_DIR, S3_BASE_URL, MAIN_ZIP_FILENAME
from src.utils.exceptions.extractor_exceptions import DownloadError
from src.logger import get_logger

logger = get_logger(__name__)


class DataDownloader:
    """
    Downloads the main Citi Bike zip file from the S3 bucket.
    
    Attributes:
        url (str): The full URL to download.
        dest_dir (Path): The local directory to save the file.
        filename (str): The name of the file to save.
    """

    def __init__(self, url: str = S3_BASE_URL + MAIN_ZIP_FILENAME, dest_dir: Path = RAW_ZIPS_DIR):
        self.url = url
        self.dest_dir = dest_dir
        self.dest_file = dest_dir / MAIN_ZIP_FILENAME

    def download(self) -> Path:
        """
        Downloads the file if it doesn't exist, then validates it.
        
        Returns:
            Path: The local path to the downloaded file.
            
        Raises:
            DownloadError: If the download fails or the file is invalid.
        """
        if self.dest_file.exists() and self._validate_file():
            logger.info(f"File already exists and is valid: {self.dest_file}")
            return self.dest_file

        logger.info(f"Starting download from {self.url}...")
        self.dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(self.url, stream=True, timeout=120)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise DownloadError(f"Network error while downloading: {e}")

        total_size = int(response.headers.get("content-length", 0))
        
        with open(self.dest_file, "wb") as f, tqdm(
            desc=self.dest_file.name,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        if not self._validate_file():
            # Clean up the bad file
            self.dest_file.unlink(missing_ok=True)
            raise DownloadError("Downloaded file failed validation (size is 0 or missing).")

        logger.info(f"Successfully downloaded to {self.dest_file}")
        return self.dest_file

    def _validate_file(self) -> bool:
        """Checks if the file exists and has a size greater than 0."""
        return self.dest_file.exists() and self.dest_file.stat().st_size > 0