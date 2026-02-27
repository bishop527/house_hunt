"""
Centralized logging configuration for House Hunt project.

Provides consistent logger setup across all modules.
"""
import logging
import sys
import time
from constants import APP_LOG_FILE, LOG_LEVEL


class UTCFormatter(logging.Formatter):
    """Logging formatter that uses UTC time instead of local time."""
    converter = time.gmtime


def setup_logger(
        name: str,
        level: int = LOG_LEVEL,
        include_console: bool = False
) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

    All timestamps are in UTC.

    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_console: If True, also log to console (stdout)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler (always present)
    file_handler = logging.FileHandler(APP_LOG_FILE)
    file_handler.setLevel(level)
    file_formatter = UTCFormatter(
        '%(asctime)s UTC [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %a'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = UTCFormatter(
            '%(asctime)s UTC [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S %a'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def silence_verbose_loggers() -> None:
    """Silence overly verbose third-party loggers."""
    logging.getLogger('googlemaps').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)