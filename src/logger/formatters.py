"""
Custom logging formatters for the ETL pipeline.
"""
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs logs as JSON strings.
    Safely handles exception tracebacks and extra dictionary fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure we capture exception info
        self._skip_log_prefix = True

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the LogRecord into a JSON string.
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "line_number":record.lineno,
            "function_name":record.funcName,
            "message": record.getMessage(),
        }

        # Safely add exception traceback if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)

        # Safely add any extra fields passed via logger.info("msg", extra={...})
        # We exclude standard LogRecord attributes to avoid duplication
        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName", 
            "levelname", "levelno", "lineno", "module", "msecs", 
            "pathname", "process", "processName", "relativeCreated", 
            "stack_info", "thread", "threadName", "exc_info", "exc_text"
        }
        
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                try:
                    # Ensure the value is JSON serializable
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data, ensure_ascii=False)


class StandardFormatter(logging.Formatter):
    """
    A human-readable formatter for console output.
    """
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )