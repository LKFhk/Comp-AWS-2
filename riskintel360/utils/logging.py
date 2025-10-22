"""
Centralized Logging Configuration for RiskIntel360
Provides timestamped log files and structured logging
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class SuppressConnectionResetFilter(logging.Filter):
    """Filter to suppress Windows ConnectionResetError from asyncio"""
    def filter(self, record):
        # Suppress ConnectionResetError from asyncio
        message = str(record.msg)
        if 'ConnectionResetError' in message:
            return False
        if 'WinError 10054' in message:
            return False
        if '_ProactorBasePipeTransport' in message:
            return False
        return True


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "riskintel360"
) -> logging.Logger:
    """
    Setup centralized logging with timestamped log files
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        app_name: Application name for log files
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"{app_name}_{timestamp}.log"
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup file handler with timestamp
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress asyncio connection reset errors (Windows issue)
    asyncio_logger = logging.getLogger('asyncio')
    asyncio_logger.addFilter(SuppressConnectionResetFilter())
    asyncio_logger.setLevel(logging.CRITICAL)  # Only show critical asyncio errors
    
    # Log startup message
    root_logger.info(f"Logging initialized - Log file: {log_file}")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info("Asyncio connection errors suppressed (Windows compatibility)")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Export functions
__all__ = ["setup_logging", "get_logger"]
