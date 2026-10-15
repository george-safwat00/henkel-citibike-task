"""
Logger Manager: Configures and manages the application's logging system.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Import our new formatters
from src.logger.formatters import JsonFormatter, StandardFormatter


class LoggerManager:
    """
    Singleton-style manager to configure the global logging system.
    """
    
    _is_configured = False

    @classmethod
    def configure(
        cls, 
        log_dir: Path = Path("logs"), 
        log_file: str = "etl_pipeline.log", 
        level: int = logging.INFO,
        max_bytes: int = 5 * 1024 * 1024,  # 5 MB per file
        backup_count: int = 3              # Keep 3 old log files
    ) -> None:
        """
        Initializes the logging system. Safe to call multiple times.
        """
        if cls._is_configured:
            return

        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / log_file

        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # 1. Console Handler -> Human-readable text
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StandardFormatter())
        root_logger.addHandler(console_handler)

        # 2. File Handler -> Machine-readable JSON
        try:
            file_handler = RotatingFileHandler(
                log_path, 
                maxBytes=max_bytes, 
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setFormatter(JsonFormatter())
            root_logger.addHandler(file_handler)
        except PermissionError:
            print(f"Warning: Could not write to {log_path}. File logging disabled.")

        cls._is_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Factory function to get a named logger.
    """
    if not LoggerManager._is_configured:
        LoggerManager.configure()
        
    return logging.getLogger(name)