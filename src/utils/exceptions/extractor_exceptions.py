"""
Custom exceptions for the ETL extraction phase.
"""

class ExtractionError(Exception):
    """Base exception for data extraction errors."""
    pass

class DownloadError(ExtractionError):
    """Raised when a file fails to download or is invalid."""
    pass

class ZipExtractionError(ExtractionError):
    """Raised when a zip file fails to extract or is corrupted."""
    pass