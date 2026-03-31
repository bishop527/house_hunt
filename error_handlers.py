"""
Centralized Error Handling Utilities

Provides consistent error handling patterns across the project.
"""
import googlemaps.exceptions
from logging_config import setup_logger

logger = setup_logger(__name__)


def handle_api_error(error, context, reraise=False):
    """
    Centralized Google Maps API error handling.

    Args:
        error (Exception): The exception that was raised
        context (str): Description of what operation failed
        reraise (bool): If True, re-raise the exception after logging

    Returns:
        None if not re-raising

    Raises:
        Exception: If reraise=True
    """
    error_type = type(error).__name__
    logger.error(f"API Error in {context}: {error_type}: {error}", exc_info=True)

    # Provide specific guidance based on error type
    if isinstance(error, googlemaps.exceptions.ApiError):
        logger.error(
            "This may be a quota, authentication, or API key issue. "
            "Check your API key and billing settings."
        )
    elif isinstance(error, googlemaps.exceptions.Timeout):
        logger.error(
            "Request timed out. This may indicate network issues or "
            "an overloaded API endpoint."
        )
    elif isinstance(error, googlemaps.exceptions.TransportError):
        logger.error(
            "Network/transport error. Check your internet connection "
            "and proxy settings."
        )
    elif isinstance(error, googlemaps.exceptions.HTTPError):
        logger.error(
            f"HTTP error. The API returned an error status code."
        )

    if reraise:
        raise

    return None


def handle_file_error(error, filepath, operation, reraise=True):
    """
    Centralized file I/O error handling.

    Args:
        error (Exception): The exception that was raised
        filepath (str): Path to the file that caused the error
        operation (str): What operation was being attempted
        reraise (bool): If True, re-raise the exception after logging

    Returns:
        None if not re-raising

    Raises:
        Exception: If reraise=True
    """
    error_type = type(error).__name__
    logger.error(
        f"File Error during {operation}: {error_type}: {error}", exc_info=True
    )
    logger.error(f"File path: {filepath}")

    # Provide specific guidance based on error type
    if isinstance(error, PermissionError):
        logger.critical(
            f"!!! PERMISSION ERROR !!!\n"
            f"Cannot {operation} {filepath}.\n"
            f"The file may be open in another program or you may lack "
            f"write permissions."
        )
    elif isinstance(error, FileNotFoundError):
        logger.error(
            f"File not found: {filepath}\n"
            f"Check that the file exists and the path is correct."
        )
    elif isinstance(error, IOError):
        logger.error(
            f"I/O error accessing {filepath}. "
            f"Check disk space and file permissions."
        )

    if reraise:
        raise

    return None


def handle_data_error(error, context, reraise=False):
    """
    Centralized data processing error handling.

    Args:
        error (Exception): The exception that was raised
        context (str): Description of what data operation failed
        reraise (bool): If True, re-raise the exception after logging

    Returns:
        None if not re-raising

    Raises:
        Exception: If reraise=True
    """
    error_type = type(error).__name__
    logger.error(f"Data Error in {context}: {error_type}: {error}", exc_info=True)

    # Provide specific guidance based on error type
    if isinstance(error, KeyError):
        logger.error(
            f"Missing expected column or key. "
            f"Check data format and column names."
        )
    elif isinstance(error, ValueError):
        logger.error(
            f"Invalid data value encountered. "
            f"Check for corrupted or malformed data."
        )
    elif isinstance(error, TypeError):
        logger.error(
            f"Type mismatch in data processing. "
            f"Check data types and conversions."
        )

    if reraise:
        raise

    return None