"""
Centralized logging configuration for House Hunt project.

Provides consistent logger setup across all modules.
"""
import logging
import sys
from constants import APP_LOG_FILE, LOG_LEVEL


def setup_logger(
        name: str,
        level: int = LOG_LEVEL,
        include_console: bool = False
) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

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
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (optional)
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def log_api_usage(
        logger: logging.Logger,
        operation: str,
        elements: int,
        cost_estimate: float = 0.0
) -> None:
    """
    Structured logging for API usage tracking.

    Args:
        logger: Logger instance to use
        operation: Name of the operation (e.g., 'distance_matrix')
        elements: Number of API elements consumed
        cost_estimate: Estimated cost in dollars
    """
    logger.info(
        f"API_USAGE | operation={operation} | "
        f"elements={elements} | estimated_cost=${cost_estimate:.4f}"
    )


def silence_verbose_loggers() -> None:
    """Silence overly verbose third-party loggers."""
    logging.getLogger('googlemaps').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)