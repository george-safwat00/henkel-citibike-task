"""
Module for extracting raw zip files into structured directories.
"""
import zipfile
from pathlib import Path

from src.config import RAW_EXTRACTED_DIR, EXPECTED_MONTHS
from src.utils.exceptions.extractor_exceptions import ZipExtractionError
from src.logger import get_logger

logger = get_logger(__name__)


class DataExtractor:
    """
    Extracts the Citi Bike zip file into monthly folders.
    """

    def __init__(self, zip_path: Path, extract_dir: Path = RAW_EXTRACTED_DIR):
        self.zip_path = zip_path
        self.extract_dir = extract_dir

    def extract(self) -> Path:
        """
        Extracts the zip file and validates the output.
        Skips extraction if the data is already present (idempotency).
        """
        if not self.zip_path.exists():
            raise ZipExtractionError(f"Zip file not found: {self.zip_path}")

        # --- IDEMPOTENCY CHECK ---
        if self._is_already_extracted():
            logger.info(f"Data already extracted to {self.extract_dir}. Skipping extraction phase.")
            return self.extract_dir

        logger.info(f"Starting extraction of {self.zip_path.name}...")
        self.extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
                csv_members = [m for m in zip_ref.namelist() if m.lower().endswith(".csv")]
                
                for member in csv_members:
                    self._extract_member(zip_ref, member)
        except zipfile.BadZipFile:
            raise ZipExtractionError(f"Corrupted or invalid zip file: {self.zip_path}")

        self._validate_extraction()
        logger.info(f"Successfully extracted to {self.extract_dir}")
        return self.extract_dir

    def _is_already_extracted(self) -> bool:
        """
        Checks if all expected month folders exist and contain at least one CSV file.
        """
        for month in EXPECTED_MONTHS:
            month_dir = self.extract_dir / month
            if not month_dir.exists():
                return False
            # Check if there is at least one CSV file in the folder
            if not any(month_dir.glob("*.csv")):
                return False
        return True

    def _extract_member(self, zip_ref: zipfile.ZipFile, member: str) -> None:
        """Extracts a single member into its corresponding month folder."""
        target_month = None
        for month in EXPECTED_MONTHS:
            if month in member:
                target_month = month
                break

        if target_month:
            filename = Path(member).name
            target_dir = self.extract_dir / target_month
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = target_dir / filename
            
            if not target_file.resolve().is_relative_to(self.extract_dir.resolve()):
                logger.warning(f"Skipping unsafe path: {member}")
                return

            with zip_ref.open(member) as source, open(target_file, "wb") as target:
                target.write(source.read())

    def _validate_extraction(self) -> None:
        """Checks if the expected month folders were created and contain files."""
        missing_months = []
        empty_months = []

        for month in EXPECTED_MONTHS:
            month_dir = self.extract_dir / month
            if not month_dir.exists():
                missing_months.append(month)
            elif not any(month_dir.iterdir()):
                empty_months.append(month)

        if missing_months:
            raise ZipExtractionError(f"Missing folders for months: {missing_months}")
        
        if empty_months:
            logger.warning(f"Extracted folders are empty for months: {empty_months}")