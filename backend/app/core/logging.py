import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'dataset_id'):
            log_entry["dataset_id"] = record.dataset_id
        if hasattr(record, 'quality_check_id'):
            log_entry["quality_check_id"] = record.quality_check_id
        
        return json.dumps(log_entry)


def setup_logging(
    level: str = "INFO",
    log_file: str = "data_quality_platform.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Setup application logging configuration"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler with JSON formatting
    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.DEBUG)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_library_loggers()
    
    logging.info("Logging configured successfully")


def configure_library_loggers():
    """Configure logging for third-party libraries"""
    
    # Reduce noise from libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("pyspark").setLevel(logging.WARNING)
    logging.getLogger("py4j").setLevel(logging.WARNING)
    
    # FastAPI and uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Add extra context to log record
        kwargs.setdefault('extra', {}).update(self.extra)
        return msg, kwargs


def get_context_logger(
    name: str,
    user_id: str = None,
    request_id: str = None,
    dataset_id: str = None,
    quality_check_id: str = None
) -> LoggerAdapter:
    """Get a logger with context information"""
    
    logger = get_logger(name)
    context = {}
    
    if user_id:
        context['user_id'] = user_id
    if request_id:
        context['request_id'] = request_id
    if dataset_id:
        context['dataset_id'] = dataset_id
    if quality_check_id:
        context['quality_check_id'] = quality_check_id
    
    return LoggerAdapter(logger, context)
