"""
Structured Logging Configuration
JSON logging with Request ID support
"""

import logging
import json
import sys
from typing import Any



class JSONFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
            
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_logging():
    """Configure application logging"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    # Remove existing handlers
    root_logger.handlers = []
    root_logger.addHandler(handler)
    
    # Set levels for third-party libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
